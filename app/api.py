from fastapi import FastAPI, UploadFile, File
from app.services.yolo_service import YoloService
from app.services.llm_service import LlmService
import shutil

app = FastAPI()

# make the services just once
yolo_service = YoloService()
llm_service = LlmService()

@app.get("/")
def home():
    return {"message": "API is running"}

@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    # save the uploaded file to a temporary place
    file_location = "temp_image.jpg"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # run YOLO detection
    results = yolo_service.detect_objects(file_location)

    return {"objects": results}

@app.post("/describe")
async def describe_image(file: UploadFile = File(...)):
    # save file again
    file_location = "temp_image.jpg"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # YOLO detection
    results = yolo_service.detect_objects(file_location)

    # LLM description
    description = llm_service.generate_description(results)

    return {
        "objects": results,
        "description": description
    }
