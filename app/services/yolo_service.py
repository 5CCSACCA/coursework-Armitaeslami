from ultralytics import YOLO
from collections import Counter

class YoloService:
    def __init__(self, model_path="yolo11n.pt"):
        self.model = YOLO(model_path)

    def detect_objects(self, image_path):
        results = self.model(image_path)

        detected_class_ids = results[0].boxes.cls.tolist()

        detected_labels = []
        for class_id in detected_class_ids:
            label_name = results[0].names[int(class_id)]
            detected_labels.append(label_name)

        object_counts = Counter(detected_labels)

        return dict(object_counts)
