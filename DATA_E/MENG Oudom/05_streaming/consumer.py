from confluent_kafka import Consumer, KafkaError
import json
import uuid
from datetime import datetime

# Configuration
KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'order_monitor_group',
    'auto.offset.reset': 'earliest'
}
TOPIC = 'orders'

def process_alert(event):
    """
    Alert Rule:
    Trigger an alert when:
    - total_amount > 500 OR
    - total_items > 20
    """
    total_amount = event.get('total_amount', 0)
    total_items = event.get('total_items', 0)
    
    if total_amount > 500 or total_items > 20:
        print(f"\n[ALERT TRIGGERED] 🚨")
        print(f"Event ID: {event['event_id']}")
        print(f"Reason: {'Amount > 500' if total_amount > 500 else ''} {'Items > 20' if total_items > 20 else ''}")
        print(f"Details: Store: {event['store']}, Total: ${total_amount}, Items: {total_items}")
        print("-" * 30)

def main():
    consumer = Consumer(KAFKA_CONFIG)
    consumer.subscribe([TOPIC])
    
    print(f"Waiting for events on topic '{TOPIC}'...")
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break
            
            # Message received
            try:
                event = json.loads(msg.value().decode('utf-8'))
                print(f"Received event: {event['event_id']} - Order {event['order_id']}")
                process_alert(event)
            except Exception as e:
                print(f"Error parsing event: {e}")
                
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
