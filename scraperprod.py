import asyncio
import pika
import re
import requests
import csv
import aiofiles

credentials = pika.PlainCredentials('rabbituser', 'rabbit1234')

# Async function to consume emails
async def consume_emails():
    connection = pika.BlockingConnection(pika.ConnectionParameters('<IP>', 5672, '/', credentials))
    channel = connection.channel()

    # Declare exchanges
    channel.exchange_declare(exchange='emails_exchange', exchange_type='fanout')

    # Declare queue for receiving emails
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='emails_exchange', queue=queue_name)

    def email_callback(channel, method, properties, body):
        email = body.decode()
        print(f" [x] Received {email}")

        # Create a task to run the async file writing operation
        asyncio.create_task(write_to_csv(email)) 

    def write_to_csv(email):
        async def _write():
            async with aiofiles.open('scraped_emails.csv', 'a', newline='') as afp:
                writer = csv.writer(afp)
                await writer.writerow([email])
        return _write()

    channel.basic_consume(queue=queue_name, on_message_callback=email_callback, auto_ack=True)    
    print(' [*] Waiting for emails. To exit press CTRL+C')
    
    # Keep the consumer running
    while True:
        connection.process_data_events(time_limit=1) 
        await asyncio.sleep(1) 

# Async function for URL scraping and distribution
async def distribute_urls():
    connection = pika.BlockingConnection(pika.ConnectionParameters('<IP>', 5672, '/', credentials))
    channel = connection.channel()
    try:
        channel.exchange_delete(exchange='urls_exchange')
    except pika.exceptions.ChannelClosedByBroker as e:
        if e.args[0] == 404:  # Exchange not found, ignore error
            pass
        else:
            raise e

    # Use a fanout exchange
    channel.exchange_declare(exchange='urls_exchange', exchange_type='fanout')  
    url_regex = r'href="https?://(?:www\.)?dlsu\.edu\.ph(?:/[^".]*(?:/|(?=$)))?"'

    base_url = "BASE_URL"
    visited = set()
    not_visited = [base_url]

    while not_visited:
        current_url = not_visited.pop(0)
        if current_url in visited:
            continue

        visited.add(current_url)

        channel.basic_publish(exchange='urls_exchange', routing_key='', body=current_url)
        print(f" [x] Sent {current_url}")

        try:
            response = requests.get(current_url, timeout=5)
            print(f"Current URL: {current_url}")
            found_urls = [url[6:-1] for url in re.findall(url_regex, response.text)]
            for url in found_urls:
                if url not in visited:
                    not_visited.append(url)
        except requests.exceptions.RequestException as e:
            print(f"Error visiting {current_url}: {e}")
        
        await asyncio.sleep(0)  # Yield to other tasks

# Main function
async def main():
    loop = asyncio.get_running_loop()
    
    # Create tasks for email consuming and URL distribution
    email_task = loop.create_task(consume_emails())
    url_task = loop.create_task(distribute_urls())

    # Run both tasks concurrently
    await asyncio.gather(email_task, url_task)

if __name__ == "__main__":
    asyncio.run(main())
