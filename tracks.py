# tracks.py
from firebase_config import db
from firebase_admin import firestore
import time

def create_track(expert_id, track_name, description, media_urls=None):
    """Expert creates a track"""
    if media_urls is None:
        media_urls = []
    
    track_id = f"track_{int(time.time() * 1000)}"
    
    new_track = {
        'trackId': track_id,
        'trackName': track_name,
        'description': description,
        'mediaUrls': media_urls,
        'createdAt': firestore.SERVER_TIMESTAMP
    }
    
    # Add to expert's tracks array
    expert_ref = db.collection('users').document(expert_id)
    expert_ref.update({
        'tracks': firestore.ArrayUnion([new_track])
    })
    
    return {'success': True, 'trackId': track_id}

def get_all_tracks():
    """Get all tracks from all experts"""
    experts = db.collection('users').where('type', '==', 'expert').stream()
    
    all_tracks = []
    for expert in experts:
        expert_data = expert.to_dict()
        expert_id = expert.id
        
        if 'tracks' in expert_data:
            for track in expert_data['tracks']:
                all_tracks.append({
                    **track,
                    'expertId': expert_id,
                    'expertName': expert_data['name']
                })
    
    return all_tracks

def enroll_in_track(learner_id, track_id, expert_id):
    """Learner enrolls in a track"""
    # Get track details from expert
    expert_ref = db.collection('users').document(expert_id)
    expert_data = expert_ref.get().to_dict()
    
    track = next((t for t in expert_data['tracks'] if t['trackId'] == track_id), None)
    
    if not track:
        return {'success': False, 'error': 'Track not found'}
    
    # Create enrollment
    enrollment = {
        'trackId': track_id,
        'expertId': expert_id,
        'trackName': track['trackName'],
        'progress': 0,
        'enrolledAt': firestore.SERVER_TIMESTAMP
    }
    
    # Add to learner's enrollments
    learner_ref = db.collection('users').document(learner_id)
    learner_ref.update({
        'enrolledTracks': firestore.ArrayUnion([enrollment])
    })
    
    return {'success': True}

def get_learner_tracks(learner_id):
    """Get learner's enrolled tracks"""
    learner_ref = db.collection('users').document(learner_id)
    learner_data = learner_ref.get().to_dict()
    
    return learner_data.get('enrolledTracks', [])

def update_progress(learner_id, track_id, new_progress):
    """Update learner's progress on a track"""
    learner_ref = db.collection('users').document(learner_id)
    learner_data = learner_ref.get().to_dict()
    
    enrolled_tracks = learner_data.get('enrolledTracks', [])
    
    # Update the specific track
    updated_tracks = []
    for enrollment in enrolled_tracks:
        if enrollment['trackId'] == track_id:
            enrollment['progress'] = new_progress
        updated_tracks.append(enrollment)
    
    learner_ref.update({'enrolledTracks': updated_tracks})
    
    return {'success': True}