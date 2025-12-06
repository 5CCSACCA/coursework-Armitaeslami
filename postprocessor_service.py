import json
import pika
import os
import time
from pymongo import MongoClient

def save_postprocessed_data(data):
    client = MongoClient("mongodb://mongodb:27017/")
    database = client["mydatabase"]
    collection = database["postprocessed"]

    collection.insert_one(data)


def add_postprocessing_fields(data):
    objects_found = data.get("objects", {})
    number_of_objects = sum(objects_found.values())

    data["number_of_objects"] = number_of_objects
    data["postprocessing_done"] = True

    return data


def start_listening():
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    queue_name = os.getenv("RABBITMQ_QUEUE", "detection_queue")

    while True:
        try:
            connection_parameters = pika.ConnectionParameters(host=rabbitmq_host)
            connection = pika.BlockingConnection(connection_parameters)
            channel = connection.channel()

            channel.queue_declare(queue=queue_name, durable=True)

            print("Postprocessor service is waiting for messages...")

            def handle_message(channel, method, properties, body):
                detection_data = json.loads(body.decode("utf-8"))

                updated_data = add_postprocessing_fields(detection_data)

                save_postprocessed_data(updated_data)

                channel.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=queue_name, on_message_callback=handle_message)
            channel.start_consuming()

        except Exception:
            print("RabbitMQ not ready. Retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    start_listening()
