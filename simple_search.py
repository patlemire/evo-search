import sys
import urllib.parse
import subprocess
import re
import html
import json
import time
import random

def search(query):
    url = "https://lite.duckduckgo.com/lite/"
    payload = {'q': query, 'kl': 'us-en', 'df': 'd'} # 'df': 'd' for past day
    data = urllib.parse.urlencode(payload)
    
    # Simple curl
    cmd = [
        "curl", "-s", "-L", 
        "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "-d", data, 
        url
    ]
    
    try:
        output = subprocess.check_output(cmd, text=True, timeout=15)
    except subprocess.CalledProcessError:
        return []

    results = []
    
    # Split by table rows roughly
    # DDG Lite structure: 
    # <tr><td><a class="result-link" href="...">Title</a></td></tr>
    # <tr><td class="result-snippet">Snippet</td></tr>
    
    lines = output.split('<tr>')
    
    current_title = None
    current_link = None
    
    for line in lines:
        # Check for link/title
        link_match = re.search(r'class="result-link" href="(.*?)">(.*?)</a>', line)
        if link_match:
            current_link = link_match.group(1)
            current_title = html.unescape(re.sub(r'<[^>]+>', '', link_match.group(2)))
            continue
            
        # Check for snippet (usually follows)
        snippet_match = re.search(r'class="result-snippet"(.*?)>(.*?)</td>', line)
        if snippet_match and current_title:
            snippet = html.unescape(re.sub(r'<[^>]+>', '', snippet_match.group(2)))
            
            results.append({
                "title": current_title,
                "url": current_link,
                "snippet": snippet
            })
            
            current_title = None
            current_link = None
            
            if len(results) >= 5:
                break
                
    return results

if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    # Strip flags if passed from other script blindly
    query = query.replace("-t d", "").replace("-c 5", "").replace("--video", "site:youtube.com")
    
    res = search(query)
    print(json.dumps(res))
