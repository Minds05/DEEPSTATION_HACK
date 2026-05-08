import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH", r"..\library-42a1f-firebase-adminsdk-fbsvc-3a0afe1ddd.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

initialize_firebase()
db = firestore.client()

def get_db():
    return db

