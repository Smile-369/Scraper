import pika
import re
import requests

credentials = pika.PlainCredentials('rabbituser', 'rabbit1234')
connection = pika.BlockingConnection(pika.ConnectionParameters('10.2.202.116', 5672, '/', credentials))
channel = connection.channel()
isAnimoConnect = False

# Declare fanout exchange
channel.exchange_declare(exchange='urls_exchange', exchange_type='fanout')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# Bind the queue to the exchange 1  (no routing key needed for fanout)
channel.queue_bind(exchange='urls_exchange', queue=queue_name)

channel.exchange_declare(exchange='emails_exchange', exchange_type='fanout')

if isAnimoConnect:
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
else:
    email_regex = r'data-cfemail="([a-fA-F0-9]+)"'

def callback(ch, method, properties, body):
    url = body.decode()  # Directly decode the URL
    print(f" [x] Received {url}")

    try:
        response = requests.get(url, timeout=5)
        emails = re.findall(email_regex, response.text)

        if emails:
            if not isAnimoConnect:
                for i in range(len(emails)):
                    emails[i] = ''.join(chr(int(emails[i][j:j+2], 16) ^ int(emails[i][:2], 16)) for j in range(2, len(emails[i]), 2))
            
            for email in emails:
                channel.basic_publish(exchange='emails_exchange', routing_key='', body=email)
                print(f" [x] Sent {email}")

    except requests.exceptions.RequestException as e:
        print(f"Error visiting {url}: {e}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
print(' [*] Waiting for URLs. To exit press CTRL+C')
channel.start_consuming()