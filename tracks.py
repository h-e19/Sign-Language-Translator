# tracks.py
from firebase_config import db
from firebase_admin import firestore
from datetime import datetime
import time

def create_track(expert_id, track_name, description, image_path=None,media_urls=None):
    try:
        """Expert creates a track"""
        if media_urls is None:
            media_urls = []
        if image_path is None: 
            image_path="static/images/placeholder1.png"
        
        track_id = f"track_{int(time.time() * 1000)}"
        
        new_track = {
            'trackId': track_id,
            'trackName': track_name,
            'description': description,
            'image_path':image_path,
            'mediaUrls': media_urls,
            'createdAt': datetime.now()
        }
        
        # Add to expert's tracks array
        expert_ref = db.collection('users').document(expert_id)
        expert_ref.update({
            'tracks': firestore.ArrayUnion([new_track])
        })
        
        return {'success': True, 'trackId': track_id}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
def delete_track(expert_id, track_id):
    """Delete a track from expert's tracks"""
    try:
        expert_ref = db.collection('users').document(expert_id)
        expert_doc = expert_ref.get()
        
        if not expert_doc.exists:
            return {'success': False, 'error': 'Expert not found'}
        
        expert_data = expert_doc.to_dict()
        tracks_list = expert_data.get('tracks', [])
        
        updated_tracks = [t for t in tracks_list if t.get('trackId') != track_id]
        
        expert_ref.update({'tracks': updated_tracks})
        
        return {'success': True}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

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
        'description':track.get('description', ''),
        'image_path': track.get('image_path', 'static/images/placeholder1.png'),
        'mediaUrls': track.get('mediaUrls', []),
        'expertName':expert_data.get("name"),
        'progress': 0,
        'completedMedia':[],
        'enrolledAt': datetime.now()
        # 'enrolledAt': firestore.SERVER_TIMESTAMP
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

def get_track_by_id(track_id):
    experts = db.collection('users').where('type', '==', 'expert').stream()
    for expert in experts:
        expert_data = expert.to_dict()
        for track in expert_data.get('tracks', []):
            if track['trackId'] == track_id:
                return {
                    "trackId": track.get("trackId"),
                    "trackName": track.get("trackName"),   
                    "description": track.get("description"), 
                    "image_path": track.get("image_path") if track.get("image_path") else "static/images/placeholder1.png",
                    "mediaUrls": track.get("mediaUrls", []),
                    "expertId": expert.id,
                    "expertName": expert_data.get("name")
                }
    return None


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

def append_media_to_track(expert_uid, track_id, media_obj):
    expert_ref = db.collection("users").document(expert_uid)
    doc = expert_ref.get()
    if not doc.exists:
        return {"success": False, "error": "Expert not found"}

    data = doc.to_dict()
    tracks = data.get("tracks", [])

    updated = []
    found = False

    for t in tracks:
        if t["trackId"] == track_id:
            found = True

            media = t.get("mediaUrls", [])
            media.append({
                "index": len(media) + 1,
                "name": media_obj["name"],
                "url": media_obj["url"]
            })

            t["mediaUrls"] = media

        updated.append(t)

    if not found:
        return {"success": False, "error": "Track not found"}

    expert_ref.update({"tracks": updated})

    return {"success": True}

def update_track_metadata(expert_uid, track_id, data):
    expert_ref = db.collection("users").document(expert_uid)
    doc = expert_ref.get()
    if not doc.exists:
        return {"success": False, "error": "expert not found"}

    user_data = doc.to_dict()
    tracks = user_data.get("tracks", [])

    new_list = []
    updated = False

    for t in tracks:
        if t["trackId"] == track_id:
            updated = True
            t.update(data)  
        new_list.append(t)

    if not updated:
        return {"success": False, "error": "Track not found"}

    expert_ref.update({"tracks": new_list})
    return {"success": True}