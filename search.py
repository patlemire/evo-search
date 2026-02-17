import sys
import json
import urllib.parse
import subprocess
import html
import re

def search_web(query, max_results=5):
    results = []
    
    # On utilise DDG Lite via une requête POST, ce qui évite certains CAPTCHAs simples sur l'URL
    search_url = "https://html.duckduckgo.com/html/"
    
    try:
        # Encodage de la requête
        payload = f"q={urllib.parse.quote(query)}"
        
        # User-Agent réaliste pour éviter le blocage "bot" trop agressif
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # Utilisation de curl pour la rapidité et la robustesse
        cmd = [
            "curl", "-s", "-L",
            "-A", user_agent,
            "-d", payload,
            search_url
        ]
        
        output = subprocess.check_output(cmd).decode('utf-8', errors='ignore')
        
        # Parsing manuel basé sur la structure DDG Lite
        # Les blocs de résultats commencent par <div class="result
        # On utilise une expression régulière globale pour trouver tous les blocs
        blocks = re.findall(r'<div class="result.*?</div>\s*</div>\s*</div>', output, re.DOTALL)
        
        for block in blocks:
            if len(results) >= max_results:
                break
                
            try:
                # 1. Extraction du lien principal (dans le titre)
                # Structure: <h2 class="result__title"><a ... href="URL">TITRE</a></h2>
                title_match = re.search(r'<h2 class="result__title">.*?href="(.*?)".*?>(.*?)</a>', block, re.DOTALL)
                if not title_match: continue
                
                raw_link = title_match.group(1)
                raw_title = title_match.group(2)
                
                # Nettoyage de l'URL DDG interne
                link = raw_link
                if 'uddg=' in raw_link:
                    parsed = urllib.parse.urlparse(raw_link)
                    query_params = urllib.parse.parse_qs(parsed.query)
                    if 'uddg' in query_params:
                        link = query_params['uddg'][0]
                elif raw_link.startswith('//'):
                    link = 'https:' + raw_link
                
                title = html.unescape(re.sub(r'<[^>]+>', '', raw_title).strip())
                
                # 3. Extraction du snippet (classe result__snippet)
                # Note: Le snippet est souvent un <a> sur DDG Lite
                snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', block, re.DOTALL)
                snippet = ""
                if snippet_match:
                    raw_snippet = snippet_match.group(1)
                    snippet = html.unescape(re.sub(r'<[^>]+>', '', raw_snippet).strip())
                
                if title and link:
                    results.append({
                        "title": title,
                        "url": link,
                        "snippet": snippet
                    })
            except Exception:
                continue
                
    except Exception as e:
        # En cas d'erreur fatale, on renvoie une liste vide
        pass
        
    return results

if __name__ == "__main__":
    try:
        # Récupération de la requête passée en argument
        query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "température Drummondville"
        
        # Exécution de la recherche
        data = search_web(query)
        
        # Sortie JSON propre garantie
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        # Fallback JSON en cas de crash complet
        print(json.dumps({"error": str(e), "results": []}))
