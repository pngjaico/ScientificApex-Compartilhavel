import os
import requests
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load API Key from .env
load_dotenv()
API_KEY = os.getenv("SCOPUS_API_KEY")
BASE_URL = "https://api.elsevier.com/content/search/scopus"

def search_scopus(query, limit=25, start=0):
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }
    params = {
        "query": query,
        "count": limit,
        "start": start
    }
    
    response = requests.get(BASE_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def format_as_markdown(data, query):
    results = data.get("search-results", {}).get("entry", [])
    md = f"# Scopus Search Results: {query}\n\n"
    md += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for entry in results:
        title = entry.get("dc:title", "No Title")
        authors = entry.get("dc:creator", "Unknown")
        journal = entry.get("prism:publicationName", "Unknown Journal")
        year = entry.get("prism:coverDate", "")[:4]
        doi = entry.get("prism:doi", "N/A")
        citations = entry.get("citedby-count", "0")
        links = entry.get("link", [])
        url = ""
        for link in links:
            if link.get("@ref") == "scopus":
                url = link.get("@href", "")
                break
        if not url and links:
            url = links[0].get("@href", "")
        
        md += f"### {title}\n"
        md += f"- **Authors:** {authors}\n"
        md += f"- **Journal:** {journal} ({year})\n"
        md += f"- **Citations:** {citations}\n"
        md += f"- **DOI:** [{doi}](https://doi.org/{doi}) if doi != 'N/A' else 'N/A'\n"
        md += f"- **Link:** [Scopus Link]({url})\n\n"
    
    return md

def main():
    parser = argparse.ArgumentParser(description="Search Scopus API")
    parser.add_argument("query", help="Scopus query string")
    parser.add_argument("--limit", type=int, default=25, help="Number of results")
    parser.add_argument("-o", "--output", help="Output file path")
    args = parser.parse_args()

    if not API_KEY:
        print("Error: SCOPUS_API_KEY not found in .env file.")
        return

    try:
        data = search_scopus(args.query, limit=args.limit)
        
        if args.output:
            if args.output.endswith(".json"):
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            else:
                md_content = format_as_markdown(data, args.query)
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(md_content)
            print(f"Results saved to {args.output}")
        else:
            print(json.dumps(data, indent=2))
            
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    main()
