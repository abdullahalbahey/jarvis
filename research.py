"""Web search helper. Results are leads, not verified evidence."""
from ddgs import DDGS


def search_web(query, max_results=5):
    results = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                title = str(item.get("title") or "").strip()
                url = str(item.get("href") or item.get("url") or "").strip()
                snippet = str(item.get("body") or item.get("snippet") or "").strip()
                if title and url:
                    results.append({"title": title[:300], "url": url[:1000], "snippet": snippet[:1200]})
    except Exception as exc:
        raise RuntimeError("Web search failed. Try again later or check search-provider availability.") from exc
    return results
