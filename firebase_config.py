# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase ONCE
if not firebase_admin._apps:
    cred = credentials.Certificate('C:\Users\hijab\Downloads\serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

# Export db instance
db = firestore.client()