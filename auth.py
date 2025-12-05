# auth.py
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime

# Initialize Firebase (do this ONCE, ideally in a separate config file)
# Check if already initialized to avoid errors
if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

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

def create_learner_doc(uid, name):
    """Create learner document (for client-side auth flow)"""
    try:
        # Get email from auth user
        user = auth.get_user(uid)
        
        db.collection('users').document(uid).set({
            'type': 'learner',
            'name': name,
            'email': user.email,
            'phoneNum': 0,
            'enrolledTracks': [],
            'createdAt': datetime.now()
        })
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_expert_doc(uid, name):
    """Create expert document (for client-side auth flow)"""
    try:
        user = auth.get_user(uid)
        
        db.collection('users').document(uid).set({
            'type': 'expert',
            'name': name,
            'email': user.email,
            'tracks': [],
            'createdAt': datetime.now()
        })
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}