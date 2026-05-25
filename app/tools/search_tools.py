from app.core.config import TAVILY_API_KEY


TAVILY_SEARCH_URL = "https://api.tavily.com/search"
SEARCH_TRIGGER_TERMS = (
    "search the internet",
    "internet search",
    "web search",
    "search web",
    "look up",
    "latest",
    "current",
    "today",
    "news",
    "price",
    "weather",
    "score",
    "schedule",
    "recent",
    "upsc",
    "prelims",
    "preliminary",
    "question paper",
    "paper",
    "exam",
    "bitcoin",
    "btc"
)


def should_search_internet(text: str) -> bool:
    normalized_text = text.lower()
    return any(term in normalized_text for term in SEARCH_TRIGGER_TERMS)


def is_bitcoin_price_query(text: str) -> bool:
    normalized_text = text.lower()
    mentions_bitcoin = "bitcoin" in normalized_text or "btc" in normalized_text
    asks_price = "price" in normalized_text or "rate" in normalized_text or "value" in normalized_text
    return mentions_bitcoin and asks_price


def _get_tavily_topic(query: str) -> str:
    normalized_query = query.lower()
    if any(term in normalized_query for term in ("stock", "share price", "market cap", "finance")):
        return "finance"
    if any(term in normalized_query for term in ("news", "latest", "today", "recent")):
        return "news"
    return "general"


def _format_tavily_result(data: dict) -> str:
    answer = (data.get("answer") or "").strip()
    results = data.get("results") or []

    parts = []
    if answer:
        parts.append(f"Answer: {answer}")

    source_lines = []
    for index, item in enumerate(results[:5], start=1):
        title = (item.get("title") or "Untitled").strip()
        url = (item.get("url") or "").strip()
        content = (item.get("content") or "").strip()

        source = f"{index}. {title}"
        if content:
            source += f" - {content}"
        if url:
            source += f" ({url})"

        source_lines.append(source)

    if source_lines:
        parts.append("Sources:\n" + "\n".join(source_lines))

    return "\n\n".join(parts) if parts else "No search results found."


async def search_internet(query: str) -> str:
    import httpx

    cleaned_query = query.strip()
    if not cleaned_query:
        return "Search query is empty."

    if not TAVILY_API_KEY:
        return "Internet search is not configured."

    if is_bitcoin_price_query(cleaned_query):
        price_result = await get_bitcoin_price()
        if not price_result.startswith("Bitcoin price lookup failed"):
            return price_result

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                TAVILY_SEARCH_URL,
                headers={
                    "Authorization": f"Bearer {TAVILY_API_KEY}",
                    "Content-Type": "application/json"
                    },
                    json={
                        "query": cleaned_query,
                        "search_depth": "basic",
                        "topic": _get_tavily_topic(cleaned_query),
                        "max_results": 5,
                        "include_answer": "basic",
                        "include_raw_content": False,
                        "include_images": False
                }
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return f"Internet search failed with status {exc.response.status_code}."
    except httpx.HTTPError as exc:
        return f"Internet search failed: {exc}"

    return _format_tavily_result(response.json())


async def get_bitcoin_price() -> str:
    import datetime
    import httpx

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "bitcoin",
                    "vs_currencies": "usd,inr",
                    "include_last_updated_at": "true"
                }
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Bitcoin price lookup failed: {exc}"

    bitcoin = response.json().get("bitcoin") or {}
    usd_price = bitcoin.get("usd")
    inr_price = bitcoin.get("inr")
    updated_at = bitcoin.get("last_updated_at")

    if usd_price is None and inr_price is None:
        return "Bitcoin price lookup failed: no price returned."

    updated_text = ""
    if updated_at:
        updated_time = datetime.datetime.fromtimestamp(
            updated_at,
            tz=datetime.timezone.utc
        )
        updated_text = f" Updated at {updated_time:%Y-%m-%d %H:%M UTC}."

    price_parts = []
    if usd_price is not None:
        price_parts.append(f"${usd_price:,.0f} USD")
    if inr_price is not None:
        price_parts.append(f"Rs {inr_price:,.0f} INR")

    return (
        "Answer: Bitcoin is currently around "
        + " / ".join(price_parts)
        + "."
        + updated_text
        + "\n\nSources:\n1. CoinGecko simple price API (https://www.coingecko.com/)"
    )


def build_search_tools():
    from langchain.tools import tool

    @tool
    async def internet_search(query: str) -> str:
        """Search the internet for current facts, news, prices, schedules, or recent information."""
        return await search_internet(query)

    return [
        internet_search
    ]
