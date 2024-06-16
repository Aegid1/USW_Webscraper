import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from datetime import datetime

# List of URLs to be scraped
urls = [
    'https://daserste.ndr.de/panorama/archiv/2010/Deutsches-Investment-Raubbau-im-Palaestinensergebiet-,panoramazement101.html',
    'https://www.tagesschau.de/ausland/europa/palaestina-staat-100.html',
    'https://www.tagesschau.de/ausland/asien/israel-gaza-evakuierung-100.html',
    'https://www.tagesschau.de/wirtschaft/weltwirtschaft/china-kritik-zoelle-e-autos-100.html'
]

def convert_date_format(date_str):
    try:
        # Try to parse the date in different formats
        date_formats = ["%d.%m.%Y", "%d. %B %Y"]
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return 'Invalid date format'
    except Exception as e:
        return str(e)

def get_article_details(url):
    try:
        # Get the page source code
        response = requests.get(url)
        response.raise_for_status()
        source = response.text

        # Create BeautifulSoup object
        soup = BeautifulSoup(source, 'html.parser')

        # Extract page title from the <title> tag
        page_title = soup.title.string if soup.title else 'Kein Seitentitel gefunden'

        # Find specific title in the content (if available)
        content_title_tag = soup.find(['h1', 'h2'])
        content_title = content_title_tag.get_text(strip=True) if content_title_tag else 'Kein Content Titel gefunden'

        # Extract publication date from the article text
        article_text = soup.get_text()
        date_pattern = re.compile(r'\b(\d{2}\.\d{2}\.\d{4}|\d{1,2}\.\s+\w+\s+\d{4})\b')
        date_match = date_pattern.search(article_text)
        date = date_match.group(0) if date_match else 'Kein Datum gefunden'
        formatted_date = convert_date_format(date) if date != 'Kein Datum gefunden' else date

        # Find author
        author = 'Kein Autor gefunden'
        author_meta_tag = soup.find('meta', attrs={'name': 'author'})
        if author_meta_tag:
            author = author_meta_tag.get('content', author)
        else:
            author_tag = soup.find('meta', property='article:author')
            if author_tag:
                author = author_tag.get('content', author)
            else:
                author_tag = soup.find(class_=re.compile(r'author', re.I))
                if author_tag:
                    author = author_tag.get_text(strip=True)

        # Extract newspaper/magazine from URL
        domain = urlparse(url).netloc
        newspaper_name = domain.replace('www.', '').split('.')[0]

        # Extract content of the article
        paragraphs = soup.find_all('p')
        content = ' '.join([para.get_text(strip=True) for para in paragraphs])

        return {
            "content": content[:500],  # Limit content length for readability
            "metadata": {
                "keywords": "test",
                "title": content_title,
                "author": author,
                "published": formatted_date,
                "url": url
            }
        }

    except Exception as e:
        return {
            'URL': url,
            'Seitentitel': 'Fehler beim Abrufen',
            'Content Titel': 'Fehler beim Abrufen',
            'Datum': 'Fehler beim Abrufen',
            'Autor': 'Fehler beim Abrufen',
            'Zeitung/Magazin': 'Fehler beim Abrufen',
            'Inhalt': str(e)
        }


# Function to send article details to the backend
def send_article_to_backend(article_details):
    api_url = ("http://localhost:4000/api/v1/articles/articles")
    response = requests.post(api_url, json=article_details)
    if response.status_code == 201:
        print(f"Successfully sent article {article_details['metadata']['url']} to backend.")
    else:
        print(f"Failed to send article {article_details['metadata']['url']} to backend. Status code: {response.status_code}")

# Iterate over the list of URLs, get details and send to backend
collection_name = "articles"
for url in urls:
    details = get_article_details(url)
    print(f"url: {details['metadata']['url']}")
    print(f"title: {details['metadata']['title']}")
    print(f"published: {details['metadata']['published']}")
    print(f"author: {details['metadata']['author']}")
    print(f"content: {details['content']}\n")
    send_article_to_backend(details)

    print(details)
