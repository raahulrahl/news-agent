# |---------------------------------------------------------|
# |                                                         |
# |                 Give Feedback / Get Help                |
# | https://github.com/getbindu/Bindu/issues/new/choose    |
# |                                                         |
# |---------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""news-agent - An Bindu Agent.

"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional


from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools import Toolkit
from agno.tools.mem0 import Mem0Tools
from agno.team import Team

from bindu.penguin.bindufy import bindufy
from dotenv import load_dotenv

from news_agent.tools import (
    get_rss_stories,
    get_all_rss_stories,
    categorize_stories_by_topic,
    generate_news_summary,
    create_sub_agent_task,
    process_sub_agent_task,
    coordinate_multi_agent_processing,
)


# Load environment variables from .env file
load_dotenv()

# Global tools instances
news_tools: Toolkit | None = None
agent: Agent | Team | None = None
model_name: str | None = None
openrouter_api_key: str | None = None
mem0_api_key: str | None = None
_initialized = False
_init_lock = asyncio.Lock()


class NewsTools(Toolkit):
    """Custom toolkit for news aggregation and analysis functions."""

    def __init__(self):
        super().__init__(name="news_tools")
        self.register(get_rss_stories)
        self.register(get_all_rss_stories)
        self.register(categorize_stories_by_topic)
        self.register(generate_news_summary)
        self.register(create_sub_agent_task)
        self.register(process_sub_agent_task)
        self.register(coordinate_multi_agent_processing)


def initialize_news_tools() -> None:
    """Initialize all news analysis tools as a Toolkit instance."""
    global news_tools

    news_tools = NewsTools()
    print("✅ News aggregation tools initialized")


def load_config() -> dict:
    """Load agent configuration from project root."""
    # Get path to agent_config.json in project root
    config_path = Path(__file__).parent / "agent_config.json"

    with open(config_path, "r") as f:
        return json.load(f)


async def initialize_agent() -> None:
    """Initialize the multi-agent news aggregation system."""
    global agent, model_name, news_tools

    if not model_name:
        msg = "model_name must be set before initializing agent"
        raise ValueError(msg)

    # Initialize news tools if not already done
    if not news_tools:
        initialize_news_tools()

    agent = Agent(
        name="Multi-Agent News Aggregation System",
        model=OpenRouter(
            id=model_name,
            api_key=openrouter_api_key,
            cache_response=True,
            supports_native_structured_outputs=True,
        ),
        tools=[
            tool
            for tool in [
                news_tools,  # News aggregation toolkit
                Mem0Tools(api_key=mem0_api_key) if mem0_api_key else None,
            ]
            if tool is not None
        ],
        description=dedent("""\
            You are an elite news aggregation and analysis coordinator with expertise in
            multi-agent systems, RSS processing, and content analysis. Your capabilities include:

            - Multi-agent coordination for parallel RSS feed processing
            - Advanced news parsing and content categorization
            - Cross-source trend analysis and pattern identification
            - Professional news summary generation
            - Real-time news aggregation from multiple high-quality sources
            - Topic clustering and emerging trend detection
            - Source-specific analysis and comparative coverage

            You coordinate a team of specialized sub-agents to process news from multiple
            RSS feeds simultaneously, categorize content, identify trends, and generate
            comprehensive summaries for executive consumption.
        """),
        instructions=dedent("""\
            1. Task Distribution Phase 🎯
               - Assess user requirements and scope of news analysis
               - Create sub-agent tasks for each RSS source (Hacker News, WSJ Tech/Markets, TechCrunch, AI News, Wired)
               - Assign specific processing instructions to each sub-agent
               - Coordinate parallel processing for maximum efficiency

            2. Multi-Agent Processing Phase 🔄
               - Monitor sub-agent progress and task completion
               - Handle errors and retry failed operations
               - Aggregate results from all sub-agents
               - Validate story extraction and categorization

            3. Analysis Phase 🔍
               - Categorize stories by topics and themes
               - Identify cross-source trends and patterns
               - Analyze category distribution and source coverage
               - Detect emerging topics and notable stories

            4. Summary Generation Phase 📝
               - Generate executive overview with key statistics
               - Create source-specific summaries with individual analysis
               - Provide cross-source trend analysis and insights
               - Format output in professional markdown structure

            5. Coordination Phase 🤝
               - Ensure all sub-agents complete their tasks
               - Aggregate individual summaries into main summary
               - Provide status updates and completion confirmation
               - Handle edge cases and partial failures gracefully

            Always:
            - Use the coordinate_multi_agent_processing function for full system operation
            - Process all RSS sources in parallel for comprehensive coverage
            - Generate structured summaries with clear executive insights
            - Handle errors gracefully and provide status updates
            - Use professional formatting with markdown structure
            - Provide actionable insights and trend analysis
        """),
        expected_output=dedent("""\
            # Multi-Agent News Summary - {Date} 📰

            ## Executive Overview
            {Global statistics and key findings}
            {Total stories processed and sources covered}
            {Overall trend analysis and emerging topics}

            ## Source-Specific Analysis
            {Individual RSS feed summaries}
            {Source-specific trends and notable stories}
            {Coverage patterns and content focus areas}

            ## Cross-Source Trends
            {Top trending topics across all sources}
            {Category distribution and frequency analysis}
            {Emerging patterns and story correlations}

            ## Key Insights
            {Actionable intelligence and strategic observations}
            {Notable stories and breaking developments}
            {Recommendations for further monitoring}

            ---
            Generated by Multi-Agent News Aggregation System
            Processing completed: {timestamp}
            Sources: {list of processed sources}
        """),
        add_datetime_to_context=True,
        markdown=True,
    )
    print("✅ Multi-Agent News Aggregation System initialized")


async def cleanup_news_tools() -> None:
    """Clean up any resources."""
    global news_tools

    if news_tools:
        print("🔌 News aggregation tools cleaned up")


async def run_agent(messages: list[dict[str, str]]) -> Any:
    """Run the agent with the given messages.

    Args:
        messages: List of message dicts with 'role' and 'content' keys

    Returns:
        Agent response
    """
    global agent

    # Run the agent and get response
    response = await agent.arun(messages)
    return response




async def handler(messages: list[dict[str, str]]) -> Any:
    """Handle incoming agent messages.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
                  e.g., [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

    Returns:
        Agent response (ManifestWorker will handle extraction)
    """
    
    # Run agent with messages
    global _initialized

    # Lazy initialization on first call (in bindufy's event loop)
    async with _init_lock:
        if not _initialized:
            print("🔧 Initializing news tools and multi-agent system...")
            # Build environment with API keys
            env = {
                **os.environ,
                #"GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY", ""),
            }
            await initialize_all(env)
            _initialized = True

    # Run the async agent
    result = await run_agent(messages)
    return result
    


async def initialize_all(env: Optional[dict[str, str]] = None):
    """Initialize news tools and agent.

    Args:
        env: Environment variables dict (not used for integrated tools)
    """
    await initialize_agent()


def main():
    """Run the Agent."""
    global model_name, api_key, mem0_api_key

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Multi-Agent News Aggregation System with Bindu Framework")
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("MODEL_NAME", "anthropic/claude-3.5-haiku"),
        help="Model ID to use (default: openai/gpt-oss-120b:free, env: MODEL_NAME), if you want you can use any free model: https://openrouter.ai/models?q=free",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("OPENROUTER_API_KEY"),
        help="OpenRouter API key (env: OPENROUTER_API_KEY)",
    )
    parser.add_argument(
        "--mem0-api-key",
        type=str,
        default=os.getenv("MEM0_API_KEY"),
        help="Mem0 API key (env: MEM0_API_KEY)",
    )
    args = parser.parse_args()

    # Set global model name and API keys
    model_name = args.model
    openrouter_api_key = args.api_key
    mem0_api_key = args.mem0_api_key

    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY required") # noqa: TRY003
    if not mem0_api_key:
        raise ValueError("MEM0_API_KEY required. Get your API key from: https://app.mem0.ai/dashboard/api-keys") # noqa: TRY003

    print(f"🤖 Multi-Agent News Aggregation System using model: {model_name}")
    print("📰 Comprehensive news processing with multi-agent coordination")
    print("🧠 Mem0 memory enabled")

    # Load configuration
    config = load_config()

    try:
        # Bindufy and start the agent server
        # Note: MCP tools and agent will be initialized lazily on first request
        print("🚀 Starting Multi-Agent News Aggregation System...")
        bindufy(config, handler)
    finally:
        # Cleanup on exit
        print("\n🧹 Cleaning up...")
        asyncio.run(cleanup_news_tools())


# Bindufy and start the agent server
if __name__ == "__main__":
    main()
