import os
import json
import base64
from google.cloud import firestore
from google.oauth2 import service_account
from fastapi import HTTPException

class Repository():
    def __init__(self):
        cred_b64 = os.getenv("FIRESTORE_CREDENTIALS_B64")
        cred_json = json.loads(base64.b64decode(cred_b64))
        credentials = service_account.Credentials.from_service_account_info(cred_json)
        self.db = firestore.Client(credentials=credentials)
        
    def get_collection(self, collection_name: str) -> list:
        docs = self.db.collection(collection_name).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    
    def get_document(self, collection_name: str, doc_id: str) -> dict:
        doc = self.db.collection(collection_name).document(doc_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        return {"id": doc.id, **doc.to_dict()}
    
    def set_document(self, collection_name: str, data: object):
        doc_ref = self.db.collection(collection_name).document()
        doc_ref.set(data)
        
    def update_document(self, collection_name: str, data: object, doc_id: str):
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc_ref.update(data)
        
    def delete_document(self, collection_name: str, doc_id: str):
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc_ref.delete()