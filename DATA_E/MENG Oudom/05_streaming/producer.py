from confluent_kafka import Producer
import json
import uuid
from datetime import datetime
import time
import random

# Configuration
KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092'
}
TOPIC = 'orders'

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def generate_event(order_id, amount, items):
    return {
        "event_id": str(uuid.uuid4()),
        "event_time": datetime.utcnow().isoformat() + "Z",
        "order_id": order_id,
        "customer_id": random.randint(1, 100),
        "store": random.choice(["Store A", "Store B", "Store C"]),
        "total_items": items,
        "total_amount": amount
    }

def main():
    producer = Producer(KAFKA_CONFIG)
    
    test_cases = [
        {"order_id": 101, "amount": 150, "items": 5},   # Regular
        {"order_id": 102, "amount": 600, "items": 10},  # Alert: Amount
        {"order_id": 103, "amount": 200, "items": 25},  # Alert: Items
        {"order_id": 104, "amount": 800, "items": 30},  # Alert: Both
    ]

    for tc in test_cases:
        event = generate_event(tc['order_id'], tc['amount'], tc['items'])
        producer.produce(
            TOPIC, 
            key=str(event['order_id']), 
            value=json.dumps(event), 
            callback=delivery_report
        )
        print(f"Produced event: {event['event_id']}")
        time.sleep(1)

    producer.flush()

if __name__ == "__main__":
    main()
