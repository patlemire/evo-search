# Evo-Search v3.0

Advanced command-line search tool with Deep Dive capabilities, date parsing, multimedia extraction, and caching.

## Features

-   **Multi-Provider**: Defaults to DuckDuckGo Lite (no API key required). Fails over to Google Custom Search if configured.
-   **Deep Dive (`--deep`)**: Fetches the actual page content of search results, cleans it (Readability), and converts it to Markdown.
-   **Media Extraction (`--media`)**: In Deep Dive mode, extracts main images (`og:image`) and video embeds (YouTube/Vimeo iframes).
-   **Smart Cache**: Results are cached locally (`.cache/results_hash.json`) for 24h to save bandwidth and speed up repeated queries.
-   **Freshness Control (`--time`)**: Filters results by date (d/w/m/y).
-   **Date Extraction**: Heuristic extraction of publication dates from HTML metadata.
-   **JSON Output**: Structured output with `source_url`, `source_title` for easy integration.

## Installation

```bash
cd skills/evo-search
pip install -r requirements.txt
```

## Usage

### Basic Search

```bash
python search.py "OpenAI latest news"
```

### Deep Dive with Media

Fetches content, main images, and video links.

```bash
python search.py "SpaceX Starship launch" --deep --media
```

### Force Refresh (Ignore Cache)

```bash
python search.py "Live sports score" --no-cache
```

### Time Filtering (Past Week)

```bash
python search.py "AI regulations" --time w
```

## Configuration

To enable Google Custom Search failover, set:

```bash
export GOOGLE_API_KEY="your_api_key"
export GOOGLE_CX="your_search_engine_id"
```

## Output Format

```json
{
  "query": "search term",
  "count": 5,
  "provider": "DDGLiteProvider",
  "cached": false,
  "results": [
    {
      "title": "Page Title",
      "source_title": "Page Title",
      "url": "https://example.com",
      "source_url": "https://example.com",
      "snippet": "Short description...",
      "source": "ddg_lite",
      "deep_content": "# Markdown Content...",
      "image_url": "https://example.com/image.jpg",
      "video_urls": ["https://youtube.com/embed/..."],
      "extracted_date": "2023-10-25T12:00:00"
    }
  ]
}
```
