import requests
import re

base_url = "https://www.dlsu.edu.ph"
isAnimoConnect = False

visited = set()
not_visited = [base_url]

scraped_emails = set()

if isAnimoConnect:
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
else:
    email_regex = r'data-cfemail="([a-fA-F0-9]+)"'
    
url_regex = r'href="https?://(?:www\.)?dlsu\.edu\.ph(?:/[^".]*(?:/|(?=$)))?"'

while not_visited:
    current_url = not_visited.pop(0)
    if current_url in visited:
        continue
    
    try:
        response = requests.get(current_url, timeout=5)
        visited.add(current_url)
        print(f"Current URL: {current_url}")
        emails = re.findall(email_regex, response.text)
        
        print(f"Emails Found on Current URL:")
        if emails:
            if not isAnimoConnect:
                for i in range(len(emails)):
                    emails[i] = ''.join(chr(int(emails[i][j:j+2], 16) ^ int(emails[i][:2], 16)) for j in range(2, len(emails[i]), 2))
            scraped_emails.update(emails)
            for email in emails:
                print(email)
        else:
            print("None")
        
        found_urls = [url[6:-1] for url in re.findall(url_regex, response.text)]
        for url in found_urls:
            if url not in visited:
                not_visited.append(url)
    
    except requests.exceptions.RequestException as e:
        print(f"Error visiting {current_url}: {e}")
    
    print(f"All Emails Found: {list(scraped_emails)}")
    print('-' * 50)