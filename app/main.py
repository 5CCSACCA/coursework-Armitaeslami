from services.yolo_service import YoloService
from services.llm_service import LlmService

def main():
    # make the classes
    yolo_service = YoloService()
    llm_service = LlmService()

    # choose an image to test
    image_file = "dog.jpg"

    print("Running YOLO object detection...")
    detected_objects = yolo_service.detect_objects(image_file)
    print("YOLO results:", detected_objects)

    print("Making the description...")
    description_text = llm_service.generate_description(detected_objects)
    print("LLM result:", description_text)

if __name__ == "__main__":
    main()
