# Evo-Search v2.0

Advanced command-line search tool with Deep Dive capabilities, date parsing, and multi-provider failover.

## Features

-   **Multi-Provider**: Defaults to DuckDuckGo Lite (no API key required). Fails over to Google Custom Search if configured.
-   **Deep Dive (`--deep`)**: Fetches the actual page content of search results, cleans it (Readability), and converts it to Markdown.
-   **Freshness Control (`--time`)**: Filters results by date (d/w/m/y).
-   **Date Extraction**: Heuristic extraction of publication dates from HTML metadata.
-   **JSON Output**: Structured output for integration with other agents or tools.

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

### Deep Dive (Fetch Content)

```bash
python search.py "Python 3.12 features" --deep
```

### Time Filtering (Past Week)

```bash
python search.py "AI regulations" --time w
```

### Configuration (Google Failover)

To enable Google Custom Search failover, set the following environment variables:

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
  "results": [
    {
      "title": "Page Title",
      "url": "https://example.com",
      "snippet": "Short description...",
      "source": "ddg_lite",
      "deep_content": "# Markdown Content...",
      "extracted_date": "2023-10-25T12:00:00"
    }
  ]
}
```
