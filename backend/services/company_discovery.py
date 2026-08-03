import os
import httpx
import logging
import re
from urllib.parse import urlparse
from typing import List, Dict, Any, Set

logger = logging.getLogger(__name__)

def normalize_url(url: str) -> str:
    """
    Normalizes a URL to avoid duplicate domains/paths (removes protocols, www, query params, trailing slashes).
    """
    if not url:
        return ""
    
    url = url.strip().lower()
    try:
        # Check if protocol is missing; if so, prefix with http:// to let urlparse work
        if not re.match(r'^[a-zA-Z]+://', url):
            parsed = urlparse("http://" + url)
        else:
            parsed = urlparse(url)
            
        host = parsed.netloc or ""
        path = parsed.path or ""
    except Exception:
        # Simple regex fallback
        cleaned = re.sub(r'^(https?://)?(www\.)?', '', url)
        return cleaned.split('?')[0].rstrip('/')

    if host.startswith("www."):
        host = host[4:]
        
    normalized = f"{host}{path}".split('?')[0].rstrip('/')
    return normalized


async def serper_search(query: str, api_key: str) -> List[Dict[str, str]]:
    """
    Performs Google Search via Serper.dev API, retrieving both organic results and local Places.
    """
    if not api_key:
        logger.warning("Serper Search API key is not configured.")
        return []

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "num": 15,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Serper API returned status {response.status_code}: {response.text}")
                return []
                
            data = response.json()
            results = []

            # 1. Parse Organic results
            if "organic" in data and isinstance(data["organic"], list):
                for item in data["organic"]:
                    results.append({
                        "title": item.get("title") or "",
                        "snippet": item.get("snippet") or "",
                        "url": item.get("link") or "",
                    })

            # 2. Parse Places results
            if "places" in data and isinstance(data["places"], list):
                for place in data["places"]:
                    snippet = f"Address: {place.get('address') or ''}. Phone: {place.get('phoneNumber') or ''}. Rating: {place.get('rating') or ''}."
                    results.append({
                        "title": place.get("title") or place.get("name") or "",
                        "snippet": snippet,
                        "url": place.get("website") or place.get("link") or "",
                    })

            return results
    except Exception as e:
        logger.error(f"Serper search failed for query '{query}': {e}")
        return []


async def discover_companies(keywords: List[str]) -> List[Dict[str, str]]:
    """
    Searches across multiple keywords and aggregates the deduplicated results.
    """
    api_key = os.getenv("SERPER_API_KEY") or ""
    if not api_key:
        logger.warning("SERPER_API_KEY environment variable is not defined.")

    # Use the first 5 keywords
    target_keywords = keywords[:5]
    
    # Run searches concurrently
    import asyncio
    search_tasks = [serper_search(kw, api_key) for kw in target_keywords]
    results_list = await asyncio.gather(*search_tasks)

    all_results = []
    seen_urls: Set[str] = set()

    for results in results_list:
        for res in results:
            url = res.get("url")
            if not url or url.strip() == "":
                continue

            normalized = normalize_url(url)
            if normalized not in seen_urls:
                seen_urls.add(normalized)
                all_results.append(res)

    return all_results
