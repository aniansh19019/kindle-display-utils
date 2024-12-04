import requests
import xml.etree.ElementTree as ET
import io
import zipfile
import datetime
import html
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin, urlparse
import pickle



BOOKS_DIR_PATH = '/mnt/us/documents/'

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

# Set of processed articles
processed_articles = set()

def parse_date(date_string):
    if date_parser:
        return date_parser.parse(date_string)
    else:
        # Custom date parsing logic
        formats_to_try = [
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',  # ISO 8601 format used by Atom
        ]
        for fmt in formats_to_try:
            try:
                return datetime.datetime.strptime(date_string, fmt)
            except ValueError:
                pass
        raise ValueError(f"Unable to parse date string: {date_string}")

def fetch_rss(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content  # Return bytes instead of text
    except requests.RequestException as e:
        print(f"Error fetching feed from {url}: {e}")
        return None

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

def fetch_image(image_url, feed_url):
    try:
        full_url = urljoin(feed_url, image_url)
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching image from {image_url}: {e}")
        return None

def parse_feed(xml_content, feed_url):
    if xml_content is None:
        return []
    
    try:
        # Parse XML content directly without escaping
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"Error parsing XML content: {e}")
        return []
    
    # Detect feed type (RSS or Atom)
    if root.tag == '{http://www.w3.org/2005/Atom}feed':
        return parse_atom(root, feed_url)
    elif root.find('channel') is not None:
        return parse_rss(root, feed_url)
    else:
        print("Error: Unable to determine feed type (RSS or Atom)")
        return []

def parse_rss(root, feed_url):
    channel = root.find('channel')
    if channel is None:
        print("Error: Unable to find 'channel' element in the RSS feed")
        return []
    
    items = channel.findall('item')
    if not items:
        print("Error: No 'item' elements found in the RSS feed")
        return []
    
    return parse_items(items, feed_url, is_atom=False)

def parse_atom(root, feed_url):
    items = root.findall('{http://www.w3.org/2005/Atom}entry')
    if not items:
        print("Error: No 'entry' elements found in the Atom feed")
        return []
    
    return parse_items(items, feed_url, is_atom=True)

def parse_items(items, feed_url, is_atom):
    parsed_items = []
    for item in items:
        guid = "NA"
        if is_atom:
            title = item.find('{http://www.w3.org/2005/Atom}title')
            description = item.find('{http://www.w3.org/2005/Atom}content')
            pub_date = item.find('{http://www.w3.org/2005/Atom}published') or item.find('{http://www.w3.org/2005/Atom}updated')
            link = item.find('{http://www.w3.org/2005/Atom}link')
            guid = item.find('{http://www.w3.org/2005/Atom}id')
        else:
            title = item.find('title')
            description = item.find('description')
            pub_date = item.find('pubDate')
            link = item.find('link')
            guid = item.find('guid')
        print(guid.text)

        # Check if article has already been processed
        if guid.text in processed_articles:
            print(f"Skipping article with GUID {guid.text}")
            continue
        else:
            processed_articles.add(guid.text)
            print(f"Processing article with GUID {guid.text}")

        # Clean and escape HTML content
        title_text = html.escape(title.text) if title is not None else 'No title'
        description_text = description.text if description is not None else 'No description'
        clean_description = clean_html(html.unescape(description_text))
        
        # Find and fetch image
        image_url = None
        if description is not None:
            soup = BeautifulSoup(description_text, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and 'src' in img_tag.attrs:
                image_url = img_tag['src']
        
        image_content = fetch_image(image_url, feed_url) if image_url else None
        
        parsed_items.append({
            'title': title_text,
            'description': clean_description,
            'pub_date': pub_date.text if pub_date is not None else 'No date',
            'link': link.get('href') if is_atom and link is not None else (link.text if link is not None else '#'),
            'image': image_content,
            'image_url': image_url
        })
    
    return parsed_items

def create_epub(feed_items, output_filename):
    epub = zipfile.ZipFile(output_filename, 'w')
    
    # Add mimetype file
    epub.writestr('mimetype', 'application/epub+zip')
    
    # Add container.xml
    epub.writestr('META-INF/container.xml', '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''')
    
    # Generate name for epub file
    epub_title = f'RSS Newsletter {datetime.datetime.now().strftime("%d %B %Y")}'
    
    # Add content.opf
    content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>{epub_title}</dc:title>
    <dc:creator>RSS Feed EPUB</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="BookID">urn:uuid:{datetime.datetime.utcnow().isoformat()}</dc:identifier>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
'''

    # Add items to manifest
    for i, (feed_url, items) in enumerate(feed_items.items()):
        content_opf += f'    <item id="feed{i}" href="feed{i}.html" media-type="application/xhtml+xml"/>\n'
        for j, item in enumerate(items):
            if item['image']:
                image_filename = f"image_{i}_{j}.jpg"
                content_opf += f'    <item id="image_{i}_{j}" href="{image_filename}" media-type="image/jpeg"/>\n'

    content_opf += '''  </manifest>
  <spine toc="ncx">
'''

    # Add items to spine
    for i in range(len(feed_items)):
        content_opf += f'    <itemref idref="feed{i}"/>\n'

    content_opf += '''  </spine>
</package>'''
    epub.writestr('OEBPS/content.opf', content_opf)
    
    # Add toc.ncx
    toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{datetime.datetime.utcnow().isoformat()}"/>
    <meta name="dtb:depth" content="2"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>RSS Feed EPUB</text>
  </docTitle>
  <navMap>
'''

    # Add nav points for each feed
    for i, (feed_url, items) in enumerate(feed_items.items()):
        feed_name = urlparse(feed_url).netloc
        toc_ncx += f'''    <navPoint id="feed{i}" playOrder="{i+1}">
      <navLabel>
        <text>{feed_name}</text>
      </navLabel>
      <content src="feed{i}.html"/>
    </navPoint>
'''

    toc_ncx += '''  </navMap>
</ncx>'''
    epub.writestr('OEBPS/toc.ncx', toc_ncx)
    
    # Add content HTML files for each feed
    for i, (feed_url, items) in enumerate(feed_items.items()):
        feed_name = urlparse(feed_url).netloc
        content_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>{feed_name}</title>
</head>
<body>
  <h1>{feed_name}</h1>
'''
    
        for j, item in enumerate(items):
            content_html += f'''
  <h2>{item['title']}</h2>
  <p><em>Published: {item['pub_date']}</em></p>
'''
            if item['image']:
                image_filename = f"image_{i}_{j}.jpg"
                content_html += f'  <img src="{image_filename}" alt="{item["title"]}"/>\n'
                epub.writestr(f'OEBPS/{image_filename}', item['image'])

            content_html += f'''
  <p>{item['description']}</p>
  <hr/>
'''
    
        content_html += '</body></html>'
        epub.writestr(f'OEBPS/feed{i}.html', content_html)
    
    epub.close()

def main():
    # import pickle data, if exists
    global processed_articles
    if os.path.exists('processed_articles.pickle'):
        with open('processed_articles.pickle', 'rb') as f:
            processed_articles = pickle.load(f)
    
    rss_urls = [
        'http://rss.cnn.com/rss/cnn_topstories.rss',
        'http://feeds.bbci.co.uk/news/rss.xml',
        'https://lwn.net/headlines/rss',
        'https://www.space.com/home/feed/site.xml',
        'https://www.newscientist.com/feed/home/?cmpid=RSS|NSNS-Home',
        'http://www.theverge.com/rss/frontpage',
        'https://feeds.arstechnica.com/arstechnica/index',
        'https://hackaday.com/blog/feed/',
        'https://hnrss.org/frontpage',
        'https://www.nasa.gov/news-release/feed/',
        'https://www.nature.com/nature.rss',
        'https://www.producthunt.com/feed',
        'https://kingstut.substack.com/feed',
        'https://xistance.substack.com/feed',
    ]
    
    all_items = {}
    for url in rss_urls:
        print(f"Fetching feed from {url}")
        xml_content = fetch_rss(url)
        if xml_content:
            items = parse_feed(xml_content, url)
            if items:
                all_items[url] = items
    
    if not all_items:
        print("No items were successfully fetched and parsed. EPUB creation aborted.")
        return
    
    # Sort items in each feed by publication date
    for url, items in all_items.items():
        try:
            all_items[url] = sorted(items, key=lambda x: parse_date(x['pub_date']), reverse=True)
        except ValueError as e:
            print(f"Error sorting items for {url}: {e}")
            print("Continuing without sorting for this feed...")
    
    epub_filename = f'rss_newsletter_{datetime.datetime.now().strftime("%d")}.epub'
    
    create_epub(all_items, epub_filename)
    print("EPUB file 'rss_feed.epub' has been created successfully.")
    # Save processed articles to pickle file
    with open('processed_articles.pickle', 'wb') as f:
        pickle.dump(processed_articles, f)

if __name__ == '__main__':
    main()
