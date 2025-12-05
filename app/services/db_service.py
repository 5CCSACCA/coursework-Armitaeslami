from pymongo import MongoClient
from datetime import datetime

class DatabaseService:
    def __init__(self):
        self.client = MongoClient("mongodb://mongodb:27017/")
        self.db = self.client["mydatabase"]
        self.collection = self.db["history"]

    def save_record(self, objects_found, description_text):
        new_record = {
            "objects": objects_found,
            "description": description_text,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.collection.insert_one(new_record)

    def get_all_records(self):
        all_items = list(self.collection.find({}, {"_id": 0}))
        return all_items
