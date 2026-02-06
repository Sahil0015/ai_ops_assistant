# Multi-Agent AI System

A multi-agent AI system built with the **Agno** framework and powered by **Groq** (LLaMA 3.3 70B).

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
│   ├── prompt.py            # System prompts for all agents
│   └── cost_tracker.py      # LLM usage cost tracking
└── tools/
    ├── weather_tool.py      # Weather data (OpenWeatherMap API)
    ├── news_tool.py         # News headlines (NewsData.io API)
    ├── github_tool.py       # GitHub data (GitHub REST API)
    ├── retry_utils.py       # API retry logic with exponential backoff
    └── cache_manager.py     # Response caching with TTL
```

## Setup

### ✅ Prerequisites

Make sure you have the following installed:

**Python 3.10**  
Check:
```bash
python --version
```

or on Windows:
```bash
py --version
```

**Git**  
Check:
```bash
git --version
```

### 📥 1. Clone the repository

```bash
git clone https://github.com/Sahil0015/ai_ops_assistant.git
cd ai_ops_assistant
```

### 🐍 2. Create and activate a virtual environment (Python 3.10)

**Windows (PowerShell)**
```powershell
py -3.10 -m venv venv
venv\Scripts\Activate
```

**macOS / Linux**
```bash
python3.10 -m venv venv
source venv/bin/activate
```

You should now see `(venv)` in your terminal.

Verify Python version:
```bash
python --version
```

Expected:
```
Python 3.10.x
```

### 📦 3. Install dependencies

Upgrade pip and install requirements:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If installation fails, ensure Python 3.10 is active and try again.

### 🔐 4. Configure environment variables

Copy the example environment file:

**macOS / Linux**
```bash
cp .env.example .env
```

**Windows (PowerShell)**
```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your API keys:
```env
GROQ_API_KEY=your_groq_api_key
WEATHER_API_KEY=your_openweathermap_api_key
NEWS_API_KEY=your_newsdata_io_api_key
GITHUB_API_KEY=your_github_personal_access_token  # optional
```

⚠️ **Do NOT commit `.env`** — it is ignored by `.gitignore`.

### 🔑 Get API Keys

- **Groq**: https://console.groq.com/keys
- **OpenWeatherMap**: https://openweathermap.org/api
- **NewsData.io**: https://newsdata.io/
- **GitHub**: https://github.com/settings/tokens

### 🔑 How to Create API Keys (Quick Guide)

You only need free-tier keys. **No payment is required.**

#### **Groq API Key**

1. Visit: https://console.groq.com/keys
2. Sign in or create an account
3. Click **Create API Key**
4. Copy the key and add it to `.env`:
   ```env
   GROQ_API_KEY=your_key_here
   ```

#### **OpenWeatherMap API Key**

1. Go to: https://openweathermap.org/api
2. Create a free account
3. Go to: https://home.openweathermap.org/api_keys and make one key
4. **Note**: Key activation may take 5–10 minutes
5. Add to `.env`:
   ```env
   WEATHER_API_KEY=your_key_here
   ```

#### **NewsData.io API Key**

1. Visit: https://newsdata.io/
2. Sign up for a free account using Google or email
3. Go to: https://newsdata.io/search-dashboard to create the API key
4. Add to `.env`:
   ```env
   NEWS_API_KEY=your_key_here
   ```

#### **GitHub API Key**

1. Go to: https://github.com/settings/personal-access-tokens
2. Generate a personal access token
3. **No scopes required** for public repositories
4. Add to `.env`:
   ```env
   GITHUB_API_KEY=your_key_here
   ```

### ▶️ 5. Run the application

```bash
streamlit run main.py
```

Once running, open your browser at:
```
http://localhost:8501
```

Click example queries in the sidebar to auto-run them.

### 🧪 6. Troubleshooting

**Port already in use**
```bash
streamlit run main.py --server.port 8502
```

**Permission or venv issues**

Windows:
```powershell
deactivate
Remove-Item -Recurse -Force venv
python -m venv venv
venv\Scripts\Activate
```

macOS/Linux:
```bash
deactivate
rm -rf venv
python3.10 -m venv venv
source venv/bin/activate
```

**Dependency issues**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Missing API Keys**

If you see an error about missing API keys:
1. Verify `.env` file exists in the project root
2. Check that all required keys are set (GROQ, WEATHER, NEWS)
3. Ensure no extra spaces around the `=` sign
4. Restart the application after adding keys

**Rate Limit Errors**

Free-tier API limits:
- **Groq**: 30 requests/minute, 14,400/day
- **OpenWeatherMap**: 60 calls/minute, 1,000,000/month
- **NewsData.io**: 200 requests/day (free tier)
- **GitHub**: 60 requests/hour (unauthenticated), 5,000/hour (authenticated)

If you hit rate limits, wait a few minutes or add authentication (GitHub).

**Stopping the Application**

Press `Ctrl+C` in the terminal where Streamlit is running.

### 🧹 7. Deactivating the environment

```bash
deactivate
```

## Features

✨ **Multi-Agent Pipeline**: Four specialized agents work together with retry logic for quality assurance

🔄 **Automatic Retry**: Verifier agent ensures response quality with up to 2 retry attempts

� **Smart Caching**: API responses are cached with TTL to reduce redundant calls and improve response times
  - Weather: 30 minutes
  - News: 10 minutes
  - GitHub: 1 hour

💰 **Cost Tracking**: Real-time tracking of LLM token usage and estimated costs per agent and session

🛠️ **Multi-Tool Support**: Combine multiple tools in a single query

📚 **README Enrichment**: GitHub user profiles and repositories automatically include README content when available, providing richer context about projects and developers

🎯 **Smart Planning**: Planner agent analyzes queries and creates optimal execution strategies

⚡ **Graceful Degradation**: Partial data fallback when verification fails after retries

## Tools

| Tool | Description | API | Auth Required |
|------|-------------|-----|---------------|
| **get_weather** | Current weather for any city | OpenWeatherMap | Yes (`WEATHER_API_KEY`) |
| **get_news** | Latest headlines by topic | NewsData.io | Yes (`NEWS_API_KEY`) |
| **GitHub Tools** | User profiles, repo search, repo info | GitHub REST API | YES (`GITHUB_API_KEY`) |

### GitHub Tool Functions

The GitHub integration provides individual functions:
- `get_github_user(username)` — Get user profile with profile README (if available)
- `search_github_users(query, max_results)` — Search for GitHub users
- `search_github_repos(query, max_results)` — Search for repositories
- `get_github_repo(owner, repo)` — Get repository details with README content (if available)

**Note**: GitHub API has rate limits (60 requests/hour without authentication, 5000 with). Authentication is recommended for better rate limits.

## Example Queries

**Single Tool Queries:**
- `"What's the weather in Tokyo?"` — Weather lookup
- `"Get me the latest AI news"` — News headlines
- `"Tell me about the GitHub user torvalds"` — User profile + profile README
- `"Search for machine learning repos on GitHub"` — Repository search
- `"Get info about the facebook/react repository"` — Repository details + README

**Multi-Tool Queries:**
- `"What's the weather in London and latest news about AI?"` — Weather + News
- `"News on AI star

## Performance Optimizations

### 🗄️ Response Caching

API responses are automatically cached to reduce redundant calls and improve response times:

- **Weather data**: Cached for 30 minutes
- **News articles**: Cached for 10 minutes
- **GitHub data**: Cached for 1 hour

**Cache Statistics** (visible in sidebar):
- Cache size and hit/miss counts
- Hit rate percentage
- Clear cache button for fresh data

**How it works**: The system generates a unique cache key from the function name and parameters. On subsequent identical requests, cached data is returned if still valid (TTL not expired).

### 💸 Cost Tracking

Real-time token usage and cost estimation for all LLM API calls:

**Groq Pricing** (per 1M tokens):
- **LLaMA 3.3 70B**: $0.59 input / $0.79 output
- **Qwen3 32B**: $0.35 input / $0.44 output

**Tracked Metrics** (visible in sidebar):
- Total session cost in USD
- Total tokens used
- Per-agent breakdown (calls, tokens, cost)

**Features**:
- Session tracking with automatic cost calculation
- Agent-level breakdown for optimization insights
- Reset session to start fresh tracking
- Estimated costs (based on character count approximation)

**Note**: Token counts are estimated using a 4:1 character-to-token ratio. Actual costs may vary slightly.tups and trending AI repos on GitHub"` — News + GitHub search

## Tech Stack

- **Framework**: [Agno](https://github.com/agno-agi/agno) v2.4.8 — Multi-agent framework
- **LLM Provider**: [Groq](https://groq.com/) — Fast inference
  - General agents: LLaMA 3.3 70B Versatile
  - Tool calling: Qwen3 32B
- **UI**: [Streamlit](https://streamlit.io/) v1.54.0
- **Python**: 3.10+

## System Requirements

- **OS**: Windows 10+, macOS 10.15+, or Linux
- **Python**: 3.10 or higher
- **RAM**: Minimum 2GB free (4GB recommended)
- **Disk Space**: ~500MB for dependencies
- **Internet**: Required for API calls

## Updates

To update the project to the latest version:

```bash
git pull origin main
pip install --upgrade -r requirements.txt
```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Open a Pull Request

## License

MIT
