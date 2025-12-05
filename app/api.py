from fastapi import FastAPI, UploadFile, File
import shutil

from app.services.yolo_service import YoloService
from app.services.llm_service import LlmService
from app.services.db_service import DatabaseService

app = FastAPI()

# create the services once
yolo_service = YoloService()
llm_service = LlmService()
db_service = DatabaseService()

@app.get("/")
def home():
    return {"message": "API is running"}

@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    file_location = "temp_image.jpg"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    results = yolo_service.detect_objects(file_location)
    return {"objects": results}

@app.post("/describe")
async def describe_image(file: UploadFile = File(...)):
    file_location = "temp_image.jpg"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    results = yolo_service.detect_objects(file_location)
    description = llm_service.generate_description(results)

    # save record in mongo
    db_service.save_record(results, description)

    return {
        "objects": results,
        "description": description
    }

@app.get("/history")
def get_history():
    records = db_service.get_all_records()
    return {"history": records}
