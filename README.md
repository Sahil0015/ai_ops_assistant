# Multi-Agent AI System

A multi-agent AI system built with the **Agno** framework and powered by **Groq** (LLaMA 3.3 70B / Qwen3 32B).

> **Assignment Reference**: See `GenAI_Intern_24h_Assignment (1).pdf` for the original requirements.

## Architecture

The system uses four specialized agents in a sequential pipeline with retry logic:

```
User Query
    │
    ▼
┌─────────────────┐
│  Planner Agent  │  ← Analyzes query, creates step-by-step plan
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Executor Agent  │  ← Executes plan using tools (Weather, News, GitHub)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Verifier Agent  │  ← Reviews response for quality & completeness
└────────┬────────┘
         │
    ┌────┴────┐
    │  PASS?  │
    └────┬────┘
         │
    ┌────┴────┐
   No        Yes
    │         │
    ▼         ▼
 Retry    ┌─────────────────┐
 (max 2)  │ Responder Agent │  ← Formats polished final response
          └────────┬────────┘
                   │
                   ▼
            Final Response
```

## Project Structure

```
├── main.py                  # Entry point — Streamlit UI
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (API keys)
├── .env.example             # Environment variable template
├── agents/
│   ├── planner_agent.py     # Planner Agent — query analysis & planning
│   ├── executor_agent.py    # Executor Agent — tool execution
│   ├── verifier_agent.py    # Verifier Agent — quality verification
│   └── responder_agent.py   # Responder Agent — final response formatting
├── llm/
│   ├── client.py            # Groq model configuration
│   └── prompt.py            # System prompts for all agents
└── tools/
    ├── weather_tool.py      # Weather data (OpenWeatherMap API)
    ├── news_tool.py         # News headlines (NewsData.io API)
    └── github_tool.py       # GitHub data (GitHub REST API)
```

## Setup

### 1. Create and activate virtual environment (Python 3.10)

```bash
# Windows
py -3.10 -m venv venv
venv\Scripts\activate

# macOS/Linux
python3.10 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API keys:
# GROQ_API_KEY=your_groq_api_key
# WEATHER_API_KEY=your_openweathermap_api_key
# NEWS_API_KEY=your_newsdata_io_api_key
# GITHUB_API_KEY=your_github_personal_access_token (optional)
```

**Get API Keys:**
- Groq: https://console.groq.com/keys
- OpenWeatherMap: https://openweathermap.org/api
- NewsData.io: https://newsdata.io/
- GitHub: https://github.com/settings/tokens (optional, for higher rate limits)

### 4. Run

```bash
streamlit run main.py
```

The app will open at http://localhost:8501. Click on example queries in the sidebar to auto-run them.

## Tools

| Tool | Description | API | Auth Required |
|------|-------------|-----|---------------|
| **get_weather** | Current weather for any city | OpenWeatherMap | Yes (`WEATHER_API_KEY`) |
| **get_news** | Latest headlines by topic | NewsData.io | Yes (`NEWS_API_KEY`) |
| **github_tool** | User profiles, repo search, repo info | GitHub REST API | Optional (`GITHUB_API_KEY`) |

### GitHub Tool Actions

The `github_tool(action, ...)` function supports:
- `get_user` — Get user profile (requires `username`)
- `search_users` — Search users (requires `query`)
- `search_repos` — Search repositories (requires `query`)
- `get_repo` — Get repository details (requires `owner`, `repo`)

## Example Queries

- `"What's the weather in Tokyo?"`
- `"Get me the latest AI news"`
- `"Tell me about the GitHub user torvalds"`
- `"Search for machine learning repos on GitHub"`
- `"Get info about the facebook/react repository"`
- `"What's the weather in London and latest news about AI?"`

## Tech Stack

- **Framework**: [Agno](https://github.com/agno-agi/agno) v2.4.8 — Multi-agent framework
- **LLM Provider**: [Groq](https://groq.com/) — Fast inference
  - General agents: LLaMA 3.3 70B Versatile
  - Tool calling: Qwen3 32B
- **UI**: [Streamlit](https://streamlit.io/) v1.54.0
- **Python**: 3.10+

## License

MIT
