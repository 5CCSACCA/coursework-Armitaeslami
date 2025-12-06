import json
import pika
import os

class RabbitMqService:
    def __init__(self):
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.queue_name = os.getenv("RABBITMQ_QUEUE", "detection_queue")

    def publish_message(self, detection_data):
        connection_parameters = pika.ConnectionParameters(host=self.rabbitmq_host)
        connection = pika.BlockingConnection(connection_parameters)
        channel = connection.channel()

        channel.queue_declare(queue=self.queue_name, durable=True)

        json_message = json.dumps(detection_data)

        channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=json_message
        )

        connection.close()


def publish_detection_to_rabbitmq(detection_data):
    service = RabbitMqService()
    service.publish_message(detection_data)
