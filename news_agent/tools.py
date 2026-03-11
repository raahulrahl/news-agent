"""News Analysis Tools - Professional RSS processing and news aggregation.

This module contains all the news processing tools from the original news-agents
project implemented directly as Agno tools with modern error handling and
parallel processing capabilities.
"""

import asyncio
import datetime
import logging
import sys
from typing import Any

import httpx
from defusedxml import ElementTree as ET
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

# =============================================================================
# Custom Exceptions
# =============================================================================


class InvalidFeedSourceError(ValueError):
    """Raised when an invalid RSS feed source is provided."""

    pass


class NoParserAvailableError(ValueError):
    """Raised when no parser is available for a feed source."""

    pass


class RSSParsingError(ValueError):
    """Raised when RSS parsing fails."""

    pass


# =============================================================================
# Constants
# =============================================================================

# RSS Feed URLs (from original news-agents)
RSS_FEEDS = {
    "hackernews": "https://news.ycombinator.com/rss",
    "wsj-tech": "https://feeds.wsj.com/rss/tech",
    "wsj-markets": "https://feeds.wsj.com/rss/markets",
    "techcrunch": "https://techcrunch.com/feed/",
    "ainews": "https://www.artificialintelligence-news.com/feed/",
    "wired": "https://www.wired.com/feed/rss",
}

# Alternative AI News feeds (fallbacks)
AI_NEWS_FALLBACKS = [
    "https://www.artificialintelligence-news.com/feed/",
    "https://venturebeat.com/ai/feed/",
    "https://www.technologyreview.com/feed/",
]

# Alternative WSJ feeds (fallbacks)
WSJ_TECH_FALLBACKS = [
    ("https://feeds.wsj.com/rss/tech", "wsj-tech"),
    ("https://feeds.dowjones.com/tech/rss", "wsj-tech"),
    ("https://www.reuters.com/technology/rss.xml", "reuters-tech"),
    ("https://techcrunch.com/category/artificial-intelligence/feed/", "techcrunch-ai"),
    ("https://feeds.bloomberg.com/technology/news.rss", "bloomberg-tech"),
]

WSJ_MARKETS_FALLBACKS = [
    ("https://feeds.wsj.com/rss/markets", "wsj-markets"),
    ("https://feeds.dowjones.com/markets/rss", "wsj-markets"),
    ("https://www.reuters.com/business/marketsNews/rss.xml", "reuters-markets"),
    ("https://feeds.bloomberg.com/markets/news.rss", "bloomberg-markets"),
    ("https://finance.yahoo.com/news/rssindex", "yahoo-finance"),
]

# HTTP Headers for browser-like requests
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# =============================================================================
# Utility Functions
# =============================================================================


def validate_feed_source(source: str) -> str:
    """Validate and normalize feed source name."""
    source = source.lower().strip()
    if source not in RSS_FEEDS:
        logger.error(f"Invalid feed source: {source}. Available: {list(RSS_FEEDS.keys())}")
        raise InvalidFeedSourceError
    return source


def get_element_text(element, tag: str, namespace: str | None = None) -> str:
    """Safely extract text from XML element with namespace support."""
    try:
        if namespace and tag in ["description", "content", "encoded"]:
            # Try different namespace patterns for content
            patterns = [
                f"{{{namespace}}}{tag}",
                f"{{{namespace}}}content:encoded",
                "content:encoded",
                "description",
            ]
            for pattern in patterns:
                found = element.find(pattern)
                if found is not None and found.text:
                    return found.text.strip()
        else:
            found = element.find(tag)
            if found is not None and found.text:
                return found.text.strip()
        return ""
    except Exception:
        return ""


def extract_image_url(item) -> str:
    """Extract image URL from RSS item (WSJ specific)."""
    try:
        # Try different image patterns
        image_patterns = [
            ".//media:content/@url",
            ".//media:thumbnail/@url",
            ".//enclosure/@url",
            ".//image/url",
        ]

        for pattern in image_patterns:
            element = item.find(pattern)
            if element is not None and element.text:
                return element.text.strip()
        return ""
    except Exception:
        return ""


def format_date_string(date_str: str) -> str | None:
    """Parse and format date string to YYYY-MM-DD format."""
    try:
        if not date_str:
            return None
        # Handle various date formats
        date_obj = datetime.datetime.fromisoformat(date_str.replace("Z", ""))
        return date_obj.strftime("%Y-%m-%d")
    except Exception:
        return date_str[:10] if date_str else None


# =============================================================================
# Retry Logic
# =============================================================================


def api_retry(func):
    """Unified retry decorator for HTTP calls."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2.0, min=2.0, max=30.0),
        retry=retry_if_exception(
            lambda e: isinstance(e, httpx.HTTPError | httpx.TimeoutException)
            or any(
                term in str(e).lower()
                for term in [
                    "timeout",
                    "connection",
                    "network",
                    "temporary",
                    "5",
                    "429",
                    "502",
                    "503",
                    "504",
                    "401",  # Unauthorized - might be temporary
                    "408",  # Request timeout
                ]
            )
        ),
    )(func)


# =============================================================================
# HTTP Client Utilities
# =============================================================================


def create_async_client(headers: dict | None = None) -> httpx.AsyncClient:
    """Create an async HTTP client with proper configuration."""
    return httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers=headers or BROWSER_HEADERS,
    )


# =============================================================================
# RSS Processing Tools
# =============================================================================


@api_retry
async def fetch_rss_content(url: str) -> str:
    """Fetch RSS content from the given URL with retry logic."""
    async with create_async_client() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def parse_hackernews_rss(content: str) -> list[dict[str, Any]]:
    """Parse Hacker News RSS feed."""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(content)
        items = []

        for item in root.findall(".//item")[:30]:  # Limit to 30 items
            title = get_element_text(item, "title")
            link = get_element_text(item, "link")
            description = get_element_text(item, "description")
            pub_date = get_element_text(item, "pubDate")

            items.append({
                "source": "hackernews",
                "title": title,
                "link": link,
                "description": description,
                "pub_date": format_date_string(pub_date),
                "category": "Technology/News",
            })

        return items
    except Exception as e:
        logger.exception("Error parsing Hacker News RSS")
        raise RSSParsingError from e


def parse_techcrunch_rss(content: str) -> list[dict[str, Any]]:
    """Parse TechCrunch RSS feed with namespaces."""
    try:
        root = ET.fromstring(content)

        # Register namespaces
        namespaces = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "wfw": "http://wellformedweb.org/CommentAPI/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "atom": "http://www.w3.org/2005/Atom",
            "sy": "http://purl.org/rss/1.0/modules/syndication/",
            "slash": "http://purl.org/rss/1.0/modules/slash/",
        }

        items = []
        for item in root.findall(".//item")[:30]:
            title = get_element_text(item, "title")
            link = get_element_text(item, "link")
            description = get_element_text(item, "description", namespaces.get("content"))
            pub_date = get_element_text(item, "pubDate")
            author = get_element_text(item, "dc:creator")

            # Extract categories
            categories = []
            for cat in item.findall(".//category"):
                if cat.text:
                    categories.append(cat.text.strip())

            items.append({
                "source": "techcrunch",
                "title": title,
                "link": link,
                "description": description,
                "pub_date": format_date_string(pub_date),
                "author": author,
                "categories": categories,
                "category": categories[0] if categories else "Technology",
            })

        return items
    except Exception as e:
        logger.exception("Error parsing TechCrunch RSS")
        raise RSSParsingError from e


def parse_generic_rss(content: str) -> list[dict[str, Any]]:
    """Parse generic RSS feed with basic elements."""
    try:
        root = ET.fromstring(content)

        items = []
        for item in root.findall(".//item")[:30]:
            title = get_element_text(item, "title")
            link = get_element_text(item, "link")
            description = get_element_text(item, "description")
            pub_date = get_element_text(item, "pubDate")
            author = get_element_text(item, "author")

            items.append({
                "title": title,
                "link": link,
                "description": description,
                "pub_date": format_date_string(pub_date),
                "author": author or "",
            })

        return items
    except Exception as e:
        logger.exception("Error parsing generic RSS")
        raise RSSParsingError from e


def parse_wsj_rss(content: str) -> list[dict[str, Any]]:
    """Parse WSJ RSS feed with multiple namespace support."""
    try:
        root = ET.fromstring(content)

        items = []
        for item in root.findall(".//item")[:30]:
            title = get_element_text(item, "title")
            link = get_element_text(item, "link")
            description = get_element_text(item, "description")
            pub_date = get_element_text(item, "pubDate")

            # Extract multiple authors with namespace handling
            authors = []
            try:
                # Try with Dublin Core namespace
                namespaces = {"dc": "http://purl.org/dc/elements/1.1/"}
                for author_elem in item.findall(".//dc:creator", namespaces):
                    if author_elem.text:
                        authors.append(author_elem.text.strip())
            except Exception:
                # Fallback: try without namespace
                for author_elem in item.findall(".//creator"):
                    if author_elem.text:
                        authors.append(author_elem.text.strip())

            # Extract image
            image_url = extract_image_url(item)

            items.append({
                "source": "wsj",
                "title": title,
                "link": link,
                "description": description,
                "pub_date": format_date_string(pub_date),
                "author": ", ".join(authors) if authors else "",
                "image_url": image_url,
            })

        return items
    except Exception as e:
        logger.exception("Error parsing WSJ RSS")
        raise RSSParsingError from e


def parse_ainews_rss(content: str) -> list[dict[str, Any]]:
    """Parse AI News RSS feed with special content extraction."""
    import html
    import re

    try:
        root = ET.fromstring(content)

        # Register content namespace
        namespaces = {"content": "http://purl.org/rss/1.0/modules/content/"}

        items = []
        for item in root.findall(".//item")[:1]:  # Only latest item
            title = get_element_text(item, "title")
            link = get_element_text(item, "link")
            description = get_element_text(item, "description", namespaces.get("content"))
            pub_date = get_element_text(item, "pubDate")

            # Extract Twitter recap from content
            twitter_recap = []
            if description:
                # Look for Twitter recap section
                recap_match = re.search(r"AI Twitter Recap[:\s]*([^<]+)", description, re.IGNORECASE)
                if recap_match:
                    recap_text = recap_match.group(1).strip()
                    # Parse bullet points
                    bullet_points = re.findall(r"[-•]\s*([^-\•\n]+)", recap_text)
                    twitter_recap = [point.strip() for point in bullet_points if point.strip()]

            # Extract categories
            categories = []
            for cat in item.findall(".//category"):
                if cat.text:
                    categories.append(cat.text.strip())

            items.append({
                "source": "ainews",
                "title": title,
                "link": link,
                "description": html.unescape(description) if description else "",
                "pub_date": format_date_string(pub_date),
                "categories": categories,
                "twitter_recap": twitter_recap,
                "category": "Artificial Intelligence",
            })

        return items
    except Exception as e:
        logger.exception("Error parsing AI News RSS")
        raise RSSParsingError from e


def parse_wired_rss(content: str) -> list[dict[str, Any]]:
    """Parse Wired RSS feed with media content."""
    try:
        root = ET.fromstring(content)

        items = []
        for item in root.findall(".//item")[:30]:
            title = get_element_text(item, "title")
            link = get_element_text(item, "link")
            description = get_element_text(item, "description")
            pub_date = get_element_text(item, "pubDate")
            author = get_element_text(item, "dc:creator")
            subject = get_element_text(item, "dc:subject")

            # Extract categories
            categories = []
            for cat in item.findall(".//category"):
                if cat.text:
                    categories.append(cat.text.strip())

            # Extract media thumbnail with proper namespace handling
            thumbnail = None
            try:
                # Try with media namespace
                namespaces = {"media": "http://search.yahoo.com/mrss/"}
                media_thumb = item.find(".//media:thumbnail", namespaces)
                if media_thumb is not None:
                    thumbnail = {
                        "url": media_thumb.get("url"),
                        "width": media_thumb.get("width"),
                        "height": media_thumb.get("height"),
                    }
            except Exception as e:
                # Fallback: try without namespace
                try:
                    media_thumb = item.find(".//thumbnail")
                    if media_thumb is not None:
                        thumbnail = {
                            "url": media_thumb.get("url"),
                            "width": media_thumb.get("width"),
                            "height": media_thumb.get("height"),
                        }
                except Exception:
                    logger.debug(f"Failed to extract thumbnail: {e}")

            items.append({
                "source": "wired",
                "title": title,
                "link": link,
                "description": description,
                "pub_date": format_date_string(pub_date),
                "author": author,
                "subject": subject,
                "categories": categories,
                "thumbnail": thumbnail,
                "category": subject or categories[0] if categories else "Technology",
            })

        return items
    except Exception as e:
        logger.exception("Error parsing Wired RSS")
        raise RSSParsingError from e


# =============================================================================
# Main RSS Processing Functions
# =============================================================================

PARSERS = {
    "hackernews": parse_hackernews_rss,
    "techcrunch": parse_techcrunch_rss,
    "wsj-tech": parse_wsj_rss,
    "wsj-markets": parse_wsj_rss,
    "ainews": parse_ainews_rss,
    "wired": parse_wired_rss,
    "bloomberg-tech": parse_generic_rss,
    "bloomberg-markets": parse_generic_rss,
    "reuters-tech": parse_generic_rss,
    "reuters-markets": parse_generic_rss,
    "techcrunch-ai": parse_techcrunch_rss,
    "yahoo-finance": parse_generic_rss,
}


async def _fetch_with_fallbacks(source: str, fallbacks: list[tuple[str, str]]) -> tuple[str | None, str]:
    """Fetch content with fallback URLs and return both content and parser type."""
    content = None
    parser_type = ""
    for url, parser in fallbacks:
        try:
            content = await fetch_rss_content(url)
            if content:
                logger.info(f"Successfully fetched from {source} fallback: {url}")
                parser_type = parser
                break
        except Exception as e:
            logger.warning(f"Failed to fetch from {url}: {e}")
            continue

    if content is None:
        logger.error(f"All {source} feeds failed")
        return None, parser_type

    return content, parser_type


async def get_rss_stories(source: str, max_stories: int = 30) -> dict[str, Any]:
    """Fetch and parse RSS stories from a specific source."""
    logger.info(f"Fetching RSS stories from {source}")

    # Fetch RSS content with fallbacks
    if source == "ainews":
        content, _ = await _fetch_with_fallbacks("AI News", [(url, "ainews") for url in AI_NEWS_FALLBACKS])
        if not content:
            return {
                "source": source,
                "total_stories": 0,
                "stories": [],
                "fetch_time": datetime.datetime.now().isoformat(),
                "error": "All AI News feeds failed",
            }
    elif source == "wsj-tech":
        content, parser_type = await _fetch_with_fallbacks("WSJ Tech", WSJ_TECH_FALLBACKS)
        if not content:
            return {
                "source": source,
                "total_stories": 0,
                "stories": [],
                "fetch_time": datetime.datetime.now().isoformat(),
                "error": "All WSJ Tech feeds failed",
            }
    elif source == "wsj-markets":
        content, parser_type = await _fetch_with_fallbacks("WSJ Markets", WSJ_MARKETS_FALLBACKS)
        if not content:
            return {
                "source": source,
                "total_stories": 0,
                "stories": [],
                "fetch_time": datetime.datetime.now().isoformat(),
                "error": "All WSJ Markets feeds failed",
            }
    else:
        # Fetch RSS content for other sources
        url = RSS_FEEDS[source]
        content = await fetch_rss_content(url)
        parser_type = source

    # Parse based on source or fallback parser type
    parser = PARSERS.get(parser_type, parse_generic_rss)
    if not parser:
        logger.error(f"No parser available for source: {parser_type}")
        raise NoParserAvailableError

    stories = parser(content)

    # Limit stories
    if max_stories > 0:
        stories = stories[:max_stories]

    return {
        "source": source,
        "total_stories": len(stories),
        "stories": stories,
        "fetch_time": datetime.datetime.now().isoformat(),
    }


async def get_all_rss_stories(max_stories_per_source: int = 30) -> dict[str, Any]:
    """Fetch and parse RSS stories from all configured sources."""
    logger.info("Fetching RSS stories from all sources")

    # Fetch all sources in parallel
    tasks = []
    for source in RSS_FEEDS:
        task = get_rss_stories(source, max_stories_per_source)
        tasks.append(task)

    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    all_stories = []
    source_results = {}
    total_stories = 0

    for _, (source, result) in enumerate(zip(RSS_FEEDS.keys(), results, strict=False)):
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch {source}: {result}")
            source_results[source] = {"source": source, "error": str(result), "stories": []}
        else:
            source_results[source] = result
            all_stories.extend(result["stories"])
            total_stories += result["total_stories"]

    return {
        "sources_processed": len(RSS_FEEDS),
        "total_stories": total_stories,
        "all_stories": all_stories,
        "source_results": source_results,
        "fetch_time": datetime.datetime.now().isoformat(),
    }


def categorize_stories_by_topic(stories: list[dict[str, Any]]) -> dict[str, Any]:
    """Categorize stories by topic and identify trends."""
    from collections import Counter

    # Extract categories
    all_categories = []
    for story in stories:
        if story.get("category"):
            all_categories.append(story["category"])
        if story.get("categories"):
            all_categories.extend(story["categories"])

    # Count categories
    category_counts = Counter(all_categories)

    # Identify top categories
    top_categories = category_counts.most_common(10)

    # Group stories by top categories
    categorized_stories = {}
    for category, _ in top_categories:
        categorized_stories[category] = [
            story for story in stories if (story.get("category") == category or category in story.get("categories", []))
        ]

    return {
        "total_categories": len(category_counts),
        "top_categories": top_categories,
        "categorized_stories": categorized_stories,
        "category_distribution": dict(category_counts),
    }


def generate_news_summary(stories: list[dict[str, Any]], summary_type: str = "comprehensive") -> str:
    """Generate a structured news summary from processed stories."""
    if not stories:
        return "No stories found to summarize."

    # Categorize stories
    categorization = categorize_stories_by_topic(stories)

    # Build summary
    summary_lines = []
    summary_lines.append(f"# News Summary - {datetime.date.today()}")
    summary_lines.append("")

    # Executive overview
    summary_lines.append("## Executive Overview")
    summary_lines.append(f"- **Total Stories Processed:** {len(stories)}")
    summary_lines.append(f"- **Sources:** {len({story['source'] for story in stories})}")
    summary_lines.append(f"- **Categories Identified:** {categorization['total_categories']}")
    summary_lines.append("")

    # Top categories
    summary_lines.append("## Top Categories")
    for category, count in categorization["top_categories"][:5]:
        summary_lines.append(f"- **{category}:** {count} stories")
    summary_lines.append("")

    # Stories by source
    summary_lines.append("## Stories by Source")
    source_counts = {}
    for story in stories:
        source = story["source"]
        source_counts[source] = source_counts.get(source, 0) + 1

    for source, count in sorted(source_counts.items()):
        summary_lines.append(f"- **{source}:** {count} stories")
    summary_lines.append("")

    # Sample stories
    summary_lines.append("## Sample Stories")
    for i, story in enumerate(stories[:10], 1):
        summary_lines.append(f"### {i}. {story.get('title', 'No title')}")
        summary_lines.append(f"**Source:** {story['source']}")
        summary_lines.append(f"**Category:** {story.get('category', 'N/A')}")
        summary_lines.append(f"**Link:** {story.get('link', 'N/A')}")
        summary_lines.append("")

    return "\n".join(summary_lines)


# =============================================================================
# Multi-Agent Coordination Tools
# =============================================================================


class AgentTask:
    """Represents a task for a sub-agent."""

    def __init__(self, task_id: str, source: str, instructions: str):
        """Initialize an agent task.

        Args:
            task_id: Unique identifier for the task
            source: RSS source to process
            instructions: Processing instructions for the sub-agent
        """
        self.task_id = task_id
        self.source = source
        self.instructions = instructions
        self.status = "pending"
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None


async def create_sub_agent_task(source: str, task_instructions: str) -> dict[str, Any]:
    """Create a task for a sub-agent to process a specific RSS source."""
    task = AgentTask(
        task_id=f"task_{source}_{datetime.datetime.now().timestamp()}", source=source, instructions=task_instructions
    )

    return {
        "task_id": task.task_id,
        "source": source,
        "instructions": task_instructions,
        "status": task.status,
        "created_at": datetime.datetime.now().isoformat(),
    }


async def process_sub_agent_task(task_id: str, source: str) -> dict[str, Any]:
    """Process a sub-agent task (simulate the actual processing)."""
    try:
        # Fetch stories for the source
        result = await get_rss_stories(source)

        # Generate summary for this source
        summary = generate_news_summary(result["stories"], f"source_{source}")

        return {
            "task_id": task_id,
            "source": source,
            "status": "completed",
            "result": {"stories": result["stories"], "summary": summary, "total_stories": result["total_stories"]},
            "completed_at": datetime.datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "task_id": task_id,
            "source": source,
            "status": "error",
            "error": str(e),
            "completed_at": datetime.datetime.now().isoformat(),
        }


async def coordinate_multi_agent_processing() -> dict[str, Any]:
    """Coordinate multi-agent RSS processing (main agent functionality)."""
    logger.info("Starting multi-agent RSS processing coordination")

    # Create tasks for each source
    tasks = []
    for source in RSS_FEEDS:
        task_instructions = f"""
        Process the RSS feed for {source}:
        1. Fetch the latest stories from the RSS feed
        2. Parse and categorize each story
        3. Generate a summary of key topics and trends
        4. Report progress and completion status

        Focus on identifying: key themes, emerging trends, notable stories, and cross-source patterns.
        """

        task = await create_sub_agent_task(source, task_instructions)
        tasks.append(task)

    # Process all tasks concurrently (simulating sub-agents)
    processing_tasks = []
    for task in tasks:
        processing_task = process_sub_agent_task(task["task_id"], task["source"])
        processing_tasks.append(processing_task)

    # Wait for all tasks to complete
    results = await asyncio.gather(*processing_tasks, return_exceptions=True)

    # Aggregate results
    all_stories = []
    source_summaries = {}
    successful_sources = []
    failed_sources = []

    for _, (source, result) in enumerate(zip(RSS_FEEDS.keys(), results, strict=False)):
        if isinstance(result, Exception):
            logger.error(f"Task failed for {source}: {result}")
            failed_sources.append({"source": source, "error": str(result)})
        elif result["status"] == "completed":
            all_stories.extend(result["result"]["stories"])
            source_summaries[source] = result["result"]["summary"]
            successful_sources.append(source)
        else:
            failed_sources.append({"source": source, "error": result.get("error", "Unknown error")})

    # Generate main summary
    main_summary = generate_news_summary(all_stories, "main_aggregated")

    return {
        "coordination_id": f"coord_{datetime.datetime.now().timestamp()}",
        "status": "completed",
        "sources_processed": len(successful_sources),
        "sources_failed": len(failed_sources),
        "total_stories": len(all_stories),
        "successful_sources": successful_sources,
        "failed_sources": failed_sources,
        "source_summaries": source_summaries,
        "main_summary": main_summary,
        "completed_at": datetime.datetime.now().isoformat(),
    }
