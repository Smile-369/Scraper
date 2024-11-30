import asyncio
import pika
import re
import requests
import csv
import aiofiles
import argparse

credentials = pika.PlainCredentials('rabbituser', 'rabbit1234')
visited = set()
scraped_emails = set()
# Async function to consume emails
async def consume_emails():
    connection = pika.BlockingConnection(pika.ConnectionParameters('10.2.202.116', 5672, '/', credentials))
    channel = connection.channel()

    # Declare exchanges
    channel.exchange_declare(exchange='emails_exchange', exchange_type='fanout')

    # Declare queue for receiving emails
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='emails_exchange', queue=queue_name)

    def email_callback(channel, method, properties, body):
        email = body.decode()
        scraped_emails.add(email)
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
    try:
        while True:
            connection.process_data_events(time_limit=1) 
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("consume_emails task cancelled")
        # Perform any necessary cleanup here, like closing the RabbitMQ connection
        channel.close()
        connection.close()

# Async function for URL scraping and distribution
async def distribute_urls(base_url):
    connection = pika.BlockingConnection(pika.ConnectionParameters('10.2.202.116', 5672, '/', credentials))
    channel = connection.channel()
    # Use a fanout exchange
    channel.exchange_declare(exchange='urls_exchange', exchange_type='fanout')  
    url_regex = r'href="https?://(?:www\.)?dlsu\.edu\.ph(?:/[^".]*(?:/|(?=$)))?"'

    base_url = base_url
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
        
        try:
            await asyncio.sleep(0) 
        except asyncio.CancelledError:
            print("distribute_urls task cancelled")
            # Add any necessary cleanup (e.g., closing RabbitMQ connection)
            channel.close() 
            connection.close()
            break  # Exit the loop since the task is cancelled

# Main function
async def main():
    parser = argparse.ArgumentParser(description='Web scraper for emails and URLs.')
    parser.add_argument('base_url', type=str, help='The base URL to start scraping from')
    parser.add_argument('duration', type=int, help='Duration (in seconds) for how long the scraper will run')
    args = parser.parse_args()

    loop = asyncio.get_running_loop()
    
    # Create tasks for email consuming and URL distribution
    email_task = loop.create_task(consume_emails())
    url_task = loop.create_task(distribute_urls(args.base_url))
    
    # Run both tasks concurrently for the specified duration
    await asyncio.gather(
        asyncio.wait_for(email_task, timeout=args.duration),
        asyncio.wait_for(url_task, timeout=args.duration)
    )

if __name__ == "__main__":
    asyncio.run(main())
    print("Completed")
    print(f"Url count: {len(visited)}")
    print(f"Email count: {len(scraped_emails)}")
    # Write the counts and contents to a txt file
    with open('scraper_output.txt', 'w') as fp:
        fp.write(f"Url count: {len(visited)}\n")
        fp.write(f"Email count: {len(scraped_emails)}\n")
        fp.write("\nVisited URLs:\n")
        for url in visited:
            fp.write(f"{url}\n")
        fp.write("\nScraped Emails:\n")
        for email in scraped_emails:
            fp.write(f"{email}\n")
