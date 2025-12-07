from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import shutil

from app.services.yolo_service import YoloService
from app.services.llm_service import LlmService
from app.services.db_service import DatabaseService
from app.services.firebase_service import FirebaseService
from app.services.rabbitmq_service import publish_detection_to_rabbitmq
from app.services.authentication_service import verify_token


app = FastAPI()

# create services
yolo_service = YoloService()
llm_service = LlmService()
db_service = DatabaseService()
firebase_service = FirebaseService()

# the security scheme for swagger
token_auth_scheme = HTTPBearer()


@app.get("/")
def home():
    return {"message": "API is running"}


@app.post("/detect")
async def detect_objects(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme)
):
    # validate token
    verify_token(f"Bearer {credentials.credentials}")

    file_location = "temp_image.jpg"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    results = yolo_service.detect_objects(file_location)
    return {"objects": results}


@app.post("/describe")
async def describe_image(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme)
):
    # validate token
    verify_token(f"Bearer {credentials.credentials}")

    file_location = "temp_image.jpg"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    results = yolo_service.detect_objects(file_location)
    description = llm_service.generate_description(results)

    db_service.save_record(results, description)
    firebase_service.save_record(results, description)

    detection_message = {
        "objects": results,
        "description": description
    }
    publish_detection_to_rabbitmq(detection_message)

    return {
        "objects": results,
        "description": description,
        "message": "Sent to RabbitMQ for post-processing"
    }


@app.get("/history")
def get_history(
    credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme)
):
    verify_token(f"Bearer {credentials.credentials}")
    records = db_service.get_all_records()
    return {"history": records}


@app.get("/firebase/history")
def firebase_history(
    credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme)
):
    verify_token(f"Bearer {credentials.credentials}")
    return firebase_service.get_all()


@app.delete("/firebase/delete/{doc_id}")
def delete_item(
    doc_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme)
):
    verify_token(f"Bearer {credentials.credentials}")
    firebase_service.delete_record(doc_id)
    return {"message": "Deleted"}


@app.put("/firebase/update/{doc_id}")
def update_item(
    doc_id: str,
    data: dict,
    credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme)
):
    verify_token(f"Bearer {credentials.credentials}")
    firebase_service.update_record(doc_id, data)
    return {"message": "Updated"}
