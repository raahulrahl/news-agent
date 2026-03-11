<p align="center">
  <img src="https://raw.githubusercontent.com/getbindu/create-bindu-agent/refs/heads/main/assets/light.svg" alt="bindu Logo" width="200">
</p>

<h1 align="center">news-agent</h1>

<p align="center">
  <strong>Multi-agent news aggregation system with comprehensive RSS processing and trend analysis</strong>
</p>

<p align="center">
  <a href="https://github.com/Paraschamoli/news-agent/actions/workflows/build-and-push.yml?query=branch%3Dmain">
    <img src="https://img.shields.io/github/actions/workflow/status/Paraschamoli/news-agent/build-and-push.yml?branch=main" alt="Build status">
  </a>
  <a href="https://img.shields.io/github/license/Paraschamoli/news-agent">
    <img src="https://img.shields.io/github/license/Paraschamoli/news-agent" alt="License">
  </a>
</p>

---

## Overview

News Agent is a sophisticated multi-agent news aggregation system built on the [Bindu Agent Framework](https://github.com/getbindu/bindu) that processes RSS feeds from multiple high-quality sources, categorizes content, identifies trends, and generates comprehensive summaries using coordinated sub-agent architecture.

**Key Capabilities:**
- 🤖 **Multi-Agent Coordination**: Parallel processing with coordinated sub-agent architecture
- 📰 **RSS Processing**: Advanced parsing of 6 major news sources with namespace support
- 🎯 **Content Analysis**: Automatic categorization and topic clustering
- 📊 **Trend Identification**: Cross-source pattern recognition and emerging topic detection
- 📝 **Professional Summaries**: Structured markdown output with executive insights
- 🔄 **Real-time Processing**: Concurrent fetching and processing with error handling

---

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- API keys for OpenRouter and Mem0 (both have free tiers)

### Installation

```bash
# Clone the repository
git clone https://github.com/Paraschamoli/news-agent.git
cd news-agent

# Create virtual environment
uv venv --python 3.12.9
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
```

### Configuration

Edit `.env` and add your API keys:

| Key | Get It From | Required |
|-----|-------------|----------|
| `OPENROUTER_API_KEY` | [OpenRouter](https://openrouter.ai/keys) | Yes |
| `MEM0_API_KEY` | [Mem0 Dashboard](https://app.mem0.ai/dashboard/api-keys) | If you want to use Mem0 tools |

### Run the Agent

```bash
# Start the agent
uv run python -m news_agent

# Agent will be available at http://localhost:3773
```

---

## Usage

### Example Queries

```bash
# Full multi-agent processing
"Process all news sources and generate a comprehensive summary"

# Trend analysis
"Analyze trending topics across all RSS feeds"

# Source-specific processing
"Get the latest stories from Hacker News and TechCrunch"

# Topic-focused analysis
"Generate a news summary focused on AI and machine learning topics"

# Comparative analysis
"Compare news coverage between different sources"

# Real-time monitoring
"Find breaking news and emerging trends in technology"
```

### Input Formats

**Plain Text:**
```
Process {source} news with {specific requirements}
```

**JSON:**
```json
{
  "content": "Get comprehensive news analysis from all sources",
  "focus": "trend-analysis"
}
```

### Output Structure

The agent returns structured output with:
- **Executive Overview**: Global statistics and key findings
- **Source-Specific Analysis**: Individual RSS feed summaries
- **Cross-Source Trends**: Topic clustering and pattern analysis
- **Key Insights**: Actionable intelligence and recommendations

---

## API Usage

The agent exposes a RESTful API when running. Default endpoint: `http://localhost:3773`

### Quick Start

For complete API documentation, request/response formats, and examples, visit:

📚 **[Bindu API Reference - Send Message to Agent](https://docs.getbindu.com/api-reference/all-the-tasks/send-message-to-agent)**

### Additional Resources

- 📖 [Full API Documentation](https://docs.getbindu.com/api-reference/all-the-tasks/send-message-to-agent)
- 📦 [Postman Collections](https://github.com/GetBindu/Bindu/tree/main/postman/collections)
- 🔧 [API Reference](https://docs.getbindu.com)

---

## Skills

### news-agents (v1.0.0)

**Primary Capability:**
- Multi-agent RSS news processing and analysis
- Parallel processing of 6 major news sources
- Advanced content categorization and trend identification

**Features:**
- 🤖 Multi-agent coordination with task distribution
- 📰 Parallel RSS processing (Hacker News, WSJ Tech/Markets, TechCrunch, AI News, Wired)
- 🎯 Advanced XML parsing with namespace support
- 📊 Automatic content categorization and topic clustering
- 🔄 Cross-source trend analysis and pattern recognition
- 📝 Professional markdown summary generation
- ⚡ Real-time news fetching with retry logic

**News Sources:**
- **Hacker News**: Technology news and discussions
- **Wall Street Journal (Tech)**: Business and technology coverage
- **Wall Street Journal (Markets)**: Financial markets and business news
- **TechCrunch**: Startup and technology industry coverage
- **AI News**: Artificial intelligence industry news and analysis
- **Wired**: Technology, science, and culture coverage

**Best Used For:**
- Daily news briefings and executive summaries
- Industry trend monitoring and analysis
- Competitive intelligence gathering
- Research and content curation
- Market sentiment analysis through news coverage

**Performance:**
- Average processing time: ~8 seconds
- Max concurrent requests: 6
- Memory per request: ~512MB
- Stories per source: 30 max

---

## Docker Deployment

### Local Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build

# Agent will be available at http://localhost:3773
```

### Docker Configuration

The agent runs on port `3773` and requires:
- `OPENROUTER_API_KEY` environment variable
- `MEM0_API_KEY` environment variable

Configure these in your `.env` file before running.

### Production Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

---

## Deploy to bindus.directory

Make your agent discoverable worldwide and enable agent-to-agent collaboration.

### Setup GitHub Secrets

```bash
# Authenticate with GitHub
gh auth login

# Set deployment secrets
gh secret set BINDU_API_TOKEN --body "<your-bindu-api-key>"
gh secret set DOCKERHUB_TOKEN --body "<your-dockerhub-token>"
```

Get your keys:
- **Bindu API Key**: [bindus.directory](https://bindus.directory) dashboard
- **Docker Hub Token**: [Docker Hub Security Settings](https://hub.docker.com/settings/security)

### Deploy

```bash
# Push to trigger automatic deployment
git push origin main
```

GitHub Actions will automatically:
1. Build your agent
2. Create Docker container
3. Push to Docker Hub
4. Register on bindus.directory

---

## Development

### Project Structure

```
news-agent/
├── news_agent/
│   ├── skills/
│   │   └── news-agents/
│   │       ├── skill.yaml          # Skill configuration
│   │       └── __init__.py
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py                     # Agent entry point
│   ├── tools.py                   # RSS processing tools
│   └── agent_config.json           # Agent configuration
├── tests/
│   └── test_main.py
├── .env.example
├── docker-compose.yml
├── Dockerfile.agent
└── pyproject.toml
```

### Running Tests

```bash
make test              # Run all tests
make test-cov          # With coverage report
```

### Code Quality

```bash
make format            # Format code with ruff
make lint              # Run linters
make check             # Format + lint + test
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually
uv run pre-commit run -a
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Powered by Bindu

Built with the [Bindu Agent Framework](https://github.com/getbindu/bindu)

**Why Bindu?**
- 🌐 **Internet of Agents**: A2A, AP2, X402 protocols for agent collaboration
- ⚡ **Zero-config setup**: From idea to production in minutes
- 🛠️ **Production-ready**: Built-in deployment, monitoring, and scaling

**Build Your Own Agent:**
```bash
uvx cookiecutter https://github.com/getbindu/create-bindu-agent.git
```

---

## Resources

- 📖 [Full Documentation](https://Paraschamoli.github.io/news-agent/)
- 💻 [GitHub Repository](https://github.com/Paraschamoli/news-agent/)
- 🐛 [Report Issues](https://github.com/Paraschamoli/news-agent/issues)
- 💬 [Join Discord](https://discord.gg/3w5zuYUuwt)
- 🌐 [Agent Directory](https://bindus.directory)
- 📚 [Bindu Documentation](https://docs.getbindu.com)

---

<p align="center">
  <strong>Built with 💛 by the team from Amsterdam 🌷</strong>
</p>

<p align="center">
  <a href="https://github.com/Paraschamoli/news-agent">⭐ Star this repo</a> •
  <a href="https://discord.gg/3w5zuYUuwt">💬 Join Discord</a> •
  <a href="https://bindus.directory">🌐 Agent Directory</a>
</p>
 
 
