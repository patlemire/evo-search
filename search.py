#!/usr/bin/env python3
import json
import urllib.parse
import urllib.request
import subprocess
import html
import re
import argparse
import sys
import os
import random
import time
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from bs4 import BeautifulSoup
from readability import Document
import html2text

# --- Configuration & Constants ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

# --- Helper Functions ---

def get_random_header_dict():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    }

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

# --- Date Extraction ---

def extract_date_from_html(html_content, url=""):
    """
    Extracts the publication date from HTML content using various heuristics:
    1. JSON-LD structured data
    2. Meta tags (article:published_time, date, etc.)
    3. URL patterns (often contain YYYY/MM/DD)
    4. Regex search in body (risky, fallback)
    Returns a datetime object or None.
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 1. JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, list): data = data[0]
                date_str = data.get('datePublished') or data.get('dateCreated') or data.get('uploadDate')
                if date_str:
                    return date_parser.parse(date_str)
            except:
                continue

        # 2. Meta Tags
        meta_targets = [
            {'property': 'article:published_time'},
            {'name': 'date'},
            {'name': 'pubdate'},
            {'name': 'original-publish-date'},
            {'name': 'publication_date'},
            {'property': 'og:published_time'},
            {'name': 'DC.date.issued'},
            {'name': 'citation_date'}
        ]
        
        for attrs in meta_targets:
            tag = soup.find('meta', attrs)
            if tag and tag.get('content'):
                try:
                    return date_parser.parse(tag['content'])
                except:
                    continue

        # 3. URL Regex (e.g., /2023/10/25/...)
        url_date = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if url_date:
            try:
                return datetime(int(url_date.group(1)), int(url_date.group(2)), int(url_date.group(3)))
            except:
                pass

        # 4. Visible Time tag
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
             try:
                return date_parser.parse(time_tag['datetime'])
             except:
                pass

    except Exception as e:
        # sys.stderr.write(f"Date extraction error: {e}\n")
        pass
    
    return None

def is_date_relevant(date_obj, time_filter):
    """
    Checks if date_obj is within the time_filter ('d', 'w', 'm', 'y').
    """
    if not date_obj:
        return True # Keep if unknown? Or strict mode? Let's keep for now.
    
    # Ensure date_obj is offset-naive for comparison or make both aware
    if date_obj.tzinfo is not None:
        date_obj = date_obj.replace(tzinfo=None)
        
    now = datetime.now()
    
    if time_filter == 'd':
        return now - date_obj <= timedelta(days=1)
    elif time_filter == 'w':
        return now - date_obj <= timedelta(weeks=1)
    elif time_filter == 'm':
        return now - date_obj <= timedelta(days=30)
    elif time_filter == 'y':
        return now - date_obj <= timedelta(days=365)
        
    return True

# --- Deep Dive Content Extraction ---

def process_deep_dive(url):
    """
    Fetches URL, extracts main content (Readability), converts to Markdown.
    Returns dict with content, author, date, etc.
    """
    try:
        response = requests.get(url, headers=get_random_header_dict(), timeout=10)
        response.raise_for_status()
        
        # Fix encoding
        if response.encoding is None:
            response.encoding = 'utf-8'
            
        html_content = response.text
        
        # Extract Metadata
        pub_date = extract_date_from_html(html_content, url)
        
        # Readability extraction
        doc = Document(html_content)
        title = doc.title()
        summary_html = doc.summary()
        
        # HTML to Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0 # No wrapping
        markdown = h.handle(summary_html)
        
        return {
            "full_content": markdown,
            "extracted_date": pub_date.isoformat() if pub_date else None,
            "extracted_title": title,
            "status": "success"
        }
    except Exception as e:
        return {
            "full_content": "",
            "error": str(e),
            "status": "error"
        }

# --- Search Providers ---

class SearchProvider:
    def search(self, query, count=5, time_filter=None):
        raise NotImplementedError

class DDGLiteProvider(SearchProvider):
    def search(self, query, count=5, time_filter=None):
        url = "https://lite.duckduckgo.com/lite/"
        payload = {'q': query, 'kl': 'us-en'}
        
        # DDG Lite supports 'df' param: d (day), w (week), m (month), y (year)
        if time_filter:
            payload['df'] = time_filter

        try:
            resp = requests.post(url, data=payload, headers=get_random_header_dict(), timeout=10)
            resp.raise_for_status()
            
            output = resp.text
            if "anomaly-modal" in output or "challenge-form" in output:
                raise Exception("DDG Rate Limit / Bot Detection")

            results = []
            rows = output.split('<tr>')
            current_result = {}
            
            for row in rows:
                if len(results) >= count: break
                
                # Link extractor
                link_match = re.search(r'<a[^>]*class="result-link"[^>]*href="(.*?)"[^>]*>(.*?)</a>', row, re.DOTALL)
                if link_match:
                    if "title" in current_result:
                        results.append(current_result)
                    
                    raw_link = link_match.group(1)
                    title = html.unescape(re.sub(r'<[^>]+>', '', link_match.group(2)).strip())
                    current_result = {"title": title, "url": raw_link, "snippet": "", "source": "ddg_lite"}
                    continue
                    
                # Snippet extractor
                if "title" in current_result:
                    snippet_match = re.search(r'class="result-snippet"[^>]*>(.*?)</td>', row, re.DOTALL)
                    if snippet_match:
                        current_result["snippet"] = html.unescape(re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip())
                        results.append(current_result)
                        current_result = {}

            if "title" in current_result and len(results) < count:
                results.append(current_result)
                
            return results
        except Exception as e:
            # sys.stderr.write(f"DDG Lite Error: {e}\n")
            raise e

class GoogleCustomSearchProvider(SearchProvider):
    def __init__(self, api_key, cx):
        self.api_key = api_key
        self.cx = cx

    def search(self, query, count=5, time_filter=None):
        if not self.api_key or not self.cx:
            raise Exception("Google API Key or CX missing")

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': query,
            'key': self.api_key,
            'cx': self.cx,
            'num': min(count, 10) # Google API max is 10
        }
        
        if time_filter:
            # Google dateRestrict: d[number], w[number], m[number]
            # Map simplified time_filter to Google format
            mapping = {'d': 'd1', 'w': 'w1', 'm': 'm1', 'y': 'y1'}
            if time_filter in mapping:
                params['dateRestrict'] = mapping[time_filter]

        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        if 'items' in data:
            for item in data['items']:
                results.append({
                    "title": item.get('title'),
                    "url": item.get('link'),
                    "snippet": item.get('snippet'),
                    "source": "google_cse"
                })
        return results

# --- Main Logic ---

def main():
    parser = argparse.ArgumentParser(description="Evo-Search v2.0")
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument("--deep", action="store_true", help="Fetch and parse page content (Deep Dive)")
    parser.add_argument("--time", "-t", choices=['d', 'w', 'm', 'y'], help="Time filter (day, week, month, year)")
    parser.add_argument("--count", "-c", type=int, default=5, help="Max results")
    parser.add_argument("--provider", choices=['ddg', 'google', 'auto'], default='auto', help="Search provider (default: auto failover)")
    
    args = parser.parse_args()
    query = " ".join(args.query)
    
    # Initialize Providers
    ddg = DDGLiteProvider()
    
    # Try to load Google Config from env or file
    google_key = os.environ.get("GOOGLE_API_KEY")
    google_cx = os.environ.get("GOOGLE_CX")
    google_provider = None
    if google_key and google_cx:
        google_provider = GoogleCustomSearchProvider(google_key, google_cx)

    results = []
    used_provider = ""

    # Search Execution with Failover
    providers_to_try = []
    
    if args.provider == 'ddg':
        providers_to_try = [ddg]
    elif args.provider == 'google':
        if google_provider: providers_to_try = [google_provider]
        else:
            print(json.dumps({"error": "Google provider requested but no API key found."}))
            return
    else: # Auto
        providers_to_try = [ddg]
        if google_provider:
            providers_to_try.append(google_provider)

    for p in providers_to_try:
        try:
            results = p.search(query, count=args.count, time_filter=args.time)
            used_provider = p.__class__.__name__
            if results: break
        except Exception:
            continue
            
    if not results:
        # Fallback: Retry DDG without time filter if it was the issue?
        # For now, just return empty or error.
        pass

    # --- Deep Dive Processing ---
    if args.deep and results:
        for res in results:
            print(f"Deep diving into: {res['url']}", file=sys.stderr)
            data = process_deep_dive(res['url'])
            
            res['deep_content'] = data['full_content']
            res['extracted_date'] = data.get('extracted_date')
            
            # Post-fetch Date Filter Check
            if args.time and data.get('extracted_date'):
                try:
                    dt = date_parser.parse(data['extracted_date'])
                    if not is_date_relevant(dt, args.time):
                        res['filtered_out'] = True
                        res['filter_reason'] = f"Date {dt} outside range {args.time}"
                except:
                    pass

    # Filter out items marked as 'filtered_out'
    final_results = [r for r in results if not r.get('filtered_out', False)]
    
    # Output
    output = {
        "query": query,
        "count": len(final_results),
        "provider": used_provider,
        "results": final_results
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    main()
