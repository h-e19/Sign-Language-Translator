# auth.py
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime
import re

# Initialize Firebase (do this ONCE, ideally in a separate config file)
# Check if already initialized to avoid errors
if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccountKey.json')
    # cred = credentials.Certificate('firebase-service-account.json')
    firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

def validate_phone_number(phone: str) -> dict:
    """Validate phone number format (E.164)"""
    try:
        # E.164 format: +[country code][number]
        # Example: +14155552671
        pattern = r'^\+[1-9]\d{1,14}$'

        if not phone:
            return {'valid': False, 'error': 'Phone number is required'}

        if not re.match(pattern, phone):
            return {'valid': False, 'error': 'Invalid phone format. Use E.164 format (e.g., +14155552671)'}

        return {'valid': True, 'phone': phone}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def create_expert(email, password, name):
    """Create expert user (server-side creation)"""
    try:
        # Create auth user
        user = auth.create_user(
            email=email,
            password=password
        )
        
        # Create Firestore document
        db.collection('users').document(user.uid).set({
            'type': 'expert',
            'name': name,
            'email': email,
            'tracks': [],
            'createdAt': datetime.now()
        })
        
        return {'success': True, 'uid': user.uid}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
#TODO: phone number to be added to sign up

def create_learner(email, password, name):
    """Create learner user (server-side creation)"""
    try:
        user = auth.create_user(
            email=email,
            password=password,
            phone_number=0  # Firebase expects format: +1234567890
        )
        
        db.collection('users').document(user.uid).set({
            'type': 'learner',
            'name': name,
            'email': email,
            'phoneNum': 0,
            'enrolledTracks': [],
            'createdAt': datetime.now()
        })
        
        return {'success': True, 'uid': user.uid}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def verify_token(id_token):
    """Verify Firebase ID token from frontend (client-side auth)"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return {'success': True, 'uid': decoded_token['uid']}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user_data(uid):
    """Get user document from Firestore"""
    try:
        doc = db.collection('users').document(uid).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        return None

def create_learner_doc(uid, name, phone_number=None):
    """Create learner document (for client-side auth flow)"""
    try:
        # Get email from auth user
        user = auth.get_user(uid)

        # Validate phone number if provided
        if phone_number:
            validation = validate_phone_number(phone_number)
            if not validation['valid']:
                return {'success': False, 'error': validation['error']}
            phone_number = validation['phone']

        db.collection('users').document(uid).set({
            'type': 'learner',
            'name': name,
            'email': user.email,
            'phoneNumber': phone_number,
            'authMethod': 'email',
            'enrolledTracks': [],
            'createdAt': datetime.now()
        })
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_expert_doc(uid, name, phone_number=None):
    """Create expert document (for client-side auth flow)"""
    try:
        user = auth.get_user(uid)

        # Validate phone number if provided
        if phone_number:
            validation = validate_phone_number(phone_number)
            if not validation['valid']:
                return {'success': False, 'error': validation['error']}
            phone_number = validation['phone']

        db.collection('users').document(uid).set({
            'type': 'expert',
            'name': name,
            'email': user.email,
            'phoneNumber': phone_number,
            'authMethod': 'email',
            'tracks': [],
            'createdAt': datetime.now()
        })
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
def create_user_doc_phone(uid, name, user_type, phone_number):
    """Create user document for phone authentication (learner or expert)"""
    try:
        # Validate phone number
        validation = validate_phone_number(phone_number)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}

        # Get user from Firebase Auth to verify phone
        user = auth.get_user(uid)

        # Base document structure
        user_doc = {
            'type': user_type,
            'name': name,
            'email': user.email if user.email else None,
            'phoneNumber': validation['phone'],
            'authMethod': 'phone',
            'createdAt': datetime.now()
        }

        # Add type-specific fields
        if user_type == 'learner':
            user_doc['enrolledTracks'] = []
        elif user_type == 'expert':
            user_doc['tracks'] = []
        else:
            return {'success': False, 'error': 'Invalid user type'}

        # Create Firestore document
        db.collection('users').document(uid).set(user_doc)
        return {'success': True}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def find_user_by_phone(phone_number: str) -> dict:
    """Find user document by phone number"""
    try:
        # Query Firestore for user with this phone number
        users_ref = db.collection('users')
        query = users_ref.where('phoneNumber', '==', phone_number).limit(1)
        results = query.stream()

        for doc in results:
            user_data = doc.to_dict()
            user_data['uid'] = doc.id  # Add the document ID
            return user_data

        return None
    except Exception as e:
        print(f"Error finding user by phone: {e}")
        return None

def link_phone_to_existing_user(uid: str, phone_number: str) -> dict:
    """Link a phone authentication to an existing user account"""
    try:
        # Update the user document to add phone auth method
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return {'success': False, 'error': 'User not found'}

        # Update to include phone as additional auth method
        user_ref.update({
            'phoneNumber': phone_number,
            'authMethod': 'email+phone'  # Both methods available
        })

        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def remove_user_track(uid, track_id: int) -> bool:
    try:
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return False

        user_data = user_doc.to_dict()
        enrolled_tracks = user_data.get('enrolledTracks', [])

        # Filter out the track to remove
        updated_tracks = [t for t in enrolled_tracks if t.get('trackId') != track_id]

        if len(updated_tracks) == len(enrolled_tracks):
            # Track not found
            return False

        # Update Firestore
        user_ref.update({'enrolledTracks': updated_tracks})
        return True

    except Exception as e:
        print("Error removing track:", e)
        return False

def send_verification_email(uid: str) -> dict:
    """Send email verification to user"""
    try:
        # Generate email verification link
        link = auth.generate_email_verification_link(
            email=auth.get_user(uid).email,
            action_code_settings=None
        )

        # Note: In production, you would send this link via email service
        # For now, Firebase handles this automatically when user signs up
        return {'success': True, 'link': link}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def check_email_verified(uid: str) -> dict:
    """Check if user's email is verified"""
    try:
        user = auth.get_user(uid)
        return {
            'success': True,
            'emailVerified': user.email_verified,
            'email': user.email
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
def check_email_verified(uid: str) -> dict:
    """Check if user's email is verified"""
    try:
        user = auth.get_user(uid)
        return {
            'success': True,
            'emailVerified': user.email_verified,
            'email': user.email
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
def update_user_email_verification(uid: str, verified: bool) -> dict:
    """Update user email verification status"""
    try:
        auth.update_user(uid, email_verified=verified)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}