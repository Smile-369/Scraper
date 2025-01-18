
# Web Scraper with RabbitMQ and Asyncio

This is an asynchronous web scraper built in Python that uses RabbitMQ for message passing. 
The scraper extracts email addresses and URLs from web pages, distributing tasks between consumers 
and producers using RabbitMQ.

## Features

- **Asynchronous URL distribution**: Uses RabbitMQ to distribute URLs among workers.
- **Email scraping**: Extracts email addresses from web pages.
- **File output**: Stores scraped emails in a CSV file and logs visited URLs and emails in a text file.
- **Extensibility**: Supports both standard email regex and decoding Cloudflare-protected email formats.

---

## Requirements

- Python 3.8+
- RabbitMQ server
- The following Python libraries:
  - `pika`
  - `requests`
  - `re`
  - `asyncio`
  - `aiofiles`
  - `argparse`

Install the dependencies using pip:

```bash
pip install pika requests aiofiles
```

---

## Usage

### Start the RabbitMQ Server
Make sure RabbitMQ is running on your system. Update the RabbitMQ credentials and host in the script if necessary.

### Run the Scraper
Use the following command to run the scraper:

```bash
python script_name.py <base_url> <duration>
```

- `<base_url>`: The URL to start scraping from.
- `<duration>`: The time (in seconds) for which the scraper will run.

### Example
```bash
python scraper.py https://example.com 300
```

---

## Outputs

1. **`scraped_emails.csv`**: Contains scraped email addresses.
2. **`scraper_output.txt`**: Logs the total counts and lists of visited URLs and scraped emails.

---

## How It Works

1. **Producers**: Scrape URLs from the base URL and publish them to the `urls_exchange` in RabbitMQ.
2. **Consumers**: Subscribe to the `urls_exchange`, fetch each URL, extract email addresses, and publish them to the `emails_exchange`.
3. **File Writing**: Emails are asynchronously written to a CSV file.

---

## Project Structure

- **Producer**: Responsible for scraping URLs and publishing them to RabbitMQ.
- **Consumer**: Fetches URLs and scrapes email addresses.
- **RabbitMQ**: Acts as the message broker for distributing URLs and emails.
- **Asyncio**: Ensures the scraper runs efficiently without blocking.

---

## Notes

- The script uses two regex patterns for extracting email addresses:
  1. Standard email regex for standard email formats.
  2. Decoding logic for Cloudflare email protection.
- Adjust the RabbitMQ parameters (`host`, `port`, `username`, and `password`) as needed.

---

## Contributing

Feel free to open issues or submit pull requests to improve the functionality or fix bugs.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
