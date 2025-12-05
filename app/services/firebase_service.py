import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

class FirebaseService:
    def __init__(self):
        # Load Firebase credentials
        cred = credentials.Certificate("firebase_key.json")
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        self.collection = self.db.collection("detections")

    def save_record(self, objects, description):
        entry = {
            "objects": objects,
            "description": description,
            "time": datetime.utcnow().isoformat()
        }
        self.collection.add(entry)

    def get_all(self):
        docs = self.collection.stream()
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]

    def delete_record(self, doc_id):
        self.collection.document(doc_id).delete()

    def update_record(self, doc_id, data):
        self.collection.document(doc_id).update(data)
