# 🤖 Trump Truth Social Market Impact Analyzer# 🤖 Trump Truth Social Market Impact Analyzer# 📊 Truthy - Social Media Market Impact Analyzer# Truth Social Monitor



AI-powered system that monitors Donald Trump's Truth Social posts and analyzes their potential market impact using **Qwen3:8b LLM** with intelligent quality checks.



![Python](https://img.shields.io/badge/Python-3.13-blue)AI-powered system that monitors Donald Trump's Truth Social posts and analyzes their potential market impact using **Qwen3:8b LLM** with intelligent quality checks.

![Qwen3](https://img.shields.io/badge/LLM-Qwen3--8B-green)

![Docker](https://img.shields.io/badge/Docker-Compose-blue)

![License](https://img.shields.io/badge/License-MIT-yellow)

![Python](https://img.shields.io/badge/Python-3.13-blue)Advanced social media monitoring system for analyzing Donald Trump's Truth Social posts for potential market impact.A Python application that monitors Truth Social posts from specified users and forwards them to Discord.

---

![Qwen3](https://img.shields.io/badge/LLM-Qwen3--8B-green)

## 🎯 Features

![Docker](https://img.shields.io/badge/Docker-Compose-blue)

### 🔍 **Multi-Layer Analysis Pipeline**

1. **Keyword Analysis** (221+ weighted keywords)![License](https://img.shields.io/badge/License-MIT-yellow)

   - Trade policy, tariffs, sanctions

   - Monetary policy, Fed actions## 🚀 Features## Features

   - Cryptocurrency regulations

   - Geopolitics, military conflicts---

   - Energy markets, commodities



2. **LLM Analysis** (Qwen3:8b - 5.2GB model)

   - Semantic understanding of market impact## 🎯 Features

   - Score calibration (0-100)

   - Urgency classification (immediate/hours/days)- **Real-time Monitoring**: Continuous monitoring of Truth Social posts- Monitors Truth Social users' posts using Mastodon-compatible API

   - Market direction predictions (stocks/crypto/forex/commodities)

   - Professional reasoning generation### 🔍 **Multi-Layer Analysis Pipeline**



3. **Quality Check** (Automated validation)1. **Keyword Analysis** (221+ weighted keywords)- **Multi-Layer Analysis**:- Forwards posts to Discord via webhooks

   - Validates analysis quality

   - Detects internal jargon   - Trade policy, tariffs, sanctions

   - Suggests improvements

   - Ensures professional output   - Monetary policy, Fed actions  - 🔍 **Keyword Analysis**: 221+ weighted keywords across critical, high, and medium impact categories- Stores processed posts in MongoDB to avoid duplicates



### 📊 **Real-time Discord Alerts**   - Cryptocurrency regulations

- Rich embeds with market analysis

- German time formatting (CET/CEST)   - Geopolitics, military conflicts  - 🤖 **LLM Analysis**: Ollama GPT-OSS:20B for intelligent semantic analysis (coming soon)- Supports media attachments (images, videos, GIFs)

- Color-coded urgency levels

- Market direction indicators   - Energy markets, commodities

- Direct links to original posts

  - 🧠 **NER Model**: Custom spaCy model trained on market-specific entities (coming soon)- Rate limiting for Discord notifications

### 💾 **Training Data Collection**

- Saves all analyses to JSONL format2. **LLM Analysis** (Qwen3:8b - 5.2GB model)

- Includes quality check results

- Ready for future spaCy NER training   - Semantic understanding of market impact- **Smart Filtering**: Whole-word matching to avoid false positives- Automatic retries for failed requests

- Tracks model performance

   - Score calibration (0-100)

---

   - Urgency classification (immediate/hours/days)- **Impact Scoring**: Comprehensive scoring system with critical trigger detection- Comprehensive error handling and logging

## 🏗️ Architecture

   - Market direction predictions (stocks/crypto/forex/commodities)

```

┌─────────────────┐   - Professional reasoning generation- **Automated Alerts**: Three-tier output system (All Posts, High Impact, Critical Alerts)

│  Truth Social   │

│   (via API)     │

└────────┬────────┘

         │3. **Quality Check** (Automated validation)## Prerequisites

         ▼

┌─────────────────┐   - Validates analysis quality

│  FlareSolverr   │ ← Cloudflare bypass

│  (Docker)       │   - Detects internal jargon## 📁 Project Structure

└────────┬────────┘

         │   - Suggests improvements

         ▼

┌─────────────────┐   - Ensures professional output- Python 3.8 or higher

│ Keyword Filter  │ ← 221+ keywords

│  (Score 0-100)  │

└────────┬────────┘

         │### 📊 **Real-time Discord Alerts**```- MongoDB instance

         ▼ (if score ≥ 20)

┌─────────────────┐- Rich embeds with market analysis

│  Qwen3:8b LLM   │ ← Semantic analysis

│  (Ollama)       │- German time formatting (CET/CEST)truthy/- Discord webhook URL

└────────┬────────┘

         │- Color-coded urgency levels

         ▼

┌─────────────────┐- Market direction indicators├── src/                          # Source code- Flaresolverr to run requests through

│ Quality Check   │ ← Validation

│  (Qwen3:8b)     │- Direct links to original posts

└────────┬────────┘

         ││   ├── analyzers/                # Analysis modules

         ▼ (if score ≥ 25)

┌─────────────────┐### 💾 **Training Data Collection**

│ Discord Alert   │ ← Rich embeds

└─────────────────┘- Saves all analyses to JSONL format│   │   ├── market_analyzer.py    # Keyword-based market analysis## Installation

```

- Includes quality check results

---

- Ready for future spaCy NER training│   │   └── llm_analyzer.py       # Ollama LLM analysis (coming soon)

## 📁 Project Structure

- Tracks model performance

```

truthy/│   ├── data/                     # Data & configuration1. Clone the repository:

├── src/

│   ├── analyzers/---

│   │   ├── market_analyzer.py    # Keyword-based analysis

│   │   └── llm_analyzer.py       # Qwen3:8b LLM integration│   │   └── keywords.py           # Comprehensive keyword database (221+ keywords)   ```bash

│   ├── data/

│   │   └── keywords.py           # 221+ weighted keywords## 🏗️ Architecture

│   ├── output/

│   │   ├── formatter.py          # Output formatting│   ├── output/                   # Output formatting   git clone https://github.com/darrenwatt/truthy.git

│   │   └── discord_notifier.py   # Discord webhook integration

│   └── config.py                 # Configuration management```

├── prompts/

│   ├── market_analysis_prompt.py # Market analysis prompt┌─────────────────┐│   │   └── formatter.py          # Result formatting and file output   cd truthy

│   ├── quality_check_prompt.py   # Quality validation prompt

│   ├── README.md                 # Prompt documentation│  Truth Social   │

│   └── QUALITY_CHECK_SUMMARY.md  # QC system details

├── tests/│   (via API)     ││   └── config.py                 # Application configuration   ```

│   ├── test_quality_check.py     # QC tests

│   ├── test_bad_analysis.py      # Negative tests└────────┬────────┘

│   └── test_llm_scenarios.py     # LLM test scenarios

├── output/                       # Generated output files         │├── tests/                        # Test suite

│   ├── truth_social_posts.txt

│   ├── market_impact_posts.txt         ▼

│   └── CRITICAL_ALERTS.txt

├── training_data/                # ML training data┌─────────────────┐│   ├── test_whole_word_matching.py2. Install dependencies:

│   └── llm_training_data.jsonl

├── main.py                       # Main entry point│  FlareSolverr   │ ← Cloudflare bypass

├── docker-compose.yaml           # Docker services

├── Makefile                      # DevOps commands│  (Docker)       ││   └── test_expanded_keywords.py   ```bash

├── requirements.txt              # Python dependencies

├── .env.example                  # Example configuration└────────┬────────┘

└── README.md                     # This file

```         │├── scripts/                      # Utility scripts   pip install -r requirements.txt



---         ▼



## 🚀 Quick Start┌─────────────────┐│   ├── analyze_posts.py          # One-time analysis   ```



### Prerequisites│ Keyword Filter  │ ← 221+ keywords



- **Python 3.13+**│  (Score 0-100)  ││   └── deep_analysis.py          # Deep historical analysis

- **Docker** & **Docker Compose**

- **Ollama** (with Qwen3:8b model)└────────┬────────┘

- **Discord Webhook** (optional, for alerts)

         │├── output/                       # Generated output files3. Create a `.env` file with your configuration:

### Installation

         ▼ (if score ≥ 20)

```bash

# 1. Clone the repository┌─────────────────┐│   ├── truth_social_posts.txt   ```env

git clone git@github.com:Muslix/social-media-analyzer.git

cd social-media-analyzer/truthy│  Qwen3:8b LLM   │ ← Semantic analysis



# 2. Install Python dependencies│  (Ollama)       ││   ├── market_impact_posts.txt   # Logging

pip install -r requirements.txt

└────────┬────────┘

# 3. Install Ollama (if not already installed)

# macOS/Linux:         ││   └── CRITICAL_ALERTS.txt   LOG_LEVEL=INFO

curl https://ollama.ai/install.sh | sh

         ▼

# Windows:

# Download from https://ollama.ai/download┌─────────────────┐├── training_data/                # ML training data storage   APPNAME="Truth Social Monitor"



# 4. Pull Qwen3:8b model (5.2GB)│ Quality Check   │ ← Validation

ollama pull qwen3:8b

│  (Qwen3:8b)     │├── main.py                       # Main entry point   ENV=PROD

# 5. Start Docker services (MongoDB + FlareSolverr)

docker compose up -d└────────┬────────┘



# 6. Configure environment         │├── run_tests.py                  # Test runner   REPEAT_DELAY=300

cp .env.example .env

# Edit .env with your settings (see Configuration section)         ▼ (if score ≥ 25)



# 7. Start the monitor┌─────────────────┐├── docker-compose.yaml           # Docker services (MongoDB, FlareSolverr)

python main.py

│ Discord Alert   │ ← Rich embeds

# Or using Make:

make full-reset  # Complete reset + start└─────────────────┘├── requirements.txt              # Python dependencies   # Discord

```

```

---

└── .env                          # Environment configuration   DISCORD_NOTIFY=true

## ⚙️ Configuration

---

### Required Setup

```   DISCORD_USERNAME="Truth Social Bot"

1. **Create `.env` file** from `.env.example`:

   ```bash## 📁 Project Structure

   cp .env.example .env

   ```   DISCORD_WEBHOOK_URL=your_webhook_url_here



2. **Configure Discord Webhook** (optional):```

   - Go to Discord Server Settings

   - Integrations → Webhooks → New Webhooktruthy/## 🛠️ Setup & Usage

   - Copy webhook URL

   - Paste into `.env`:├── src/

     ```env

     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN│   ├── analyzers/   # MongoDB

     ```

│   │   ├── market_analyzer.py    # Keyword-based analysis

3. **Key Settings** in `.env`:

   ```env│   │   └── llm_analyzer.py       # Qwen3:8b LLM integration### Quick Start   MONGO_DBSTRING=mongodb://localhost:27017/

   # Truth Social

   TRUTH_USERNAME=realDonaldTrump│   ├── data/

   

   # Ollama│   │   └── keywords.py           # 221+ weighted keywords   MONGO_DB=truthsocial

   OLLAMA_MODEL=qwen3:8b

   OLLAMA_URL=http://localhost:11434│   ├── output/

   

   # Discord (set to false to disable)│   │   ├── formatter.py          # Output formatting```bash   MONGO_COLLECTION=posts

   DISCORD_NOTIFY=true

   DISCORD_WEBHOOK_URL=your_webhook_url│   │   └── discord_notifier.py   # Discord webhook integration

   

   # Thresholds│   └── config.py                 # Configuration management# Start Docker services

   LLM_THRESHOLD=20      # Minimum keyword score for LLM

   DISCORD_THRESHOLD=25  # Minimum LLM score for alerts├── prompts/

   

   # Quality Check (optional)│   ├── market_analysis_prompt.py # Market analysis promptdocker-compose up -d   # Truth Social

   QUALITY_CHECK_ENABLED=true

   ```│   ├── quality_check_prompt.py   # Quality validation prompt



See `.env.example` for all available options.│   ├── README.md                 # Prompt documentation   TRUTH_USERNAME=username_to_monitor



---│   └── QUALITY_CHECK_SUMMARY.md  # QC system details



## 📖 Usage├── tests/# Run the monitor   TRUTH_INSTANCE=truthsocial.com



### Basic Commands│   ├── test_quality_check.py     # QC tests



```bash│   ├── test_bad_analysis.py      # Negative testspython main.py

# Start the monitor

python main.py│   └── test_llm_scenarios.py     # LLM test scenarios



# Run with Make├── output/                       # Generated output files   # Request Settings

make start           # Start application

make full-reset      # Docker restart + DB clear + start│   ├── truth_social_posts.txt

make test            # Run LLM test scenarios

make test-quality-check  # Test quality check system│   ├── market_impact_posts.txt# Run tests   REQUEST_TIMEOUT=30

make status          # Check all services

make clean-db        # Clear MongoDB database│   └── CRITICAL_ALERTS.txt

make training-stats  # Show training data statistics

```├── training_data/                # ML training datapython run_tests.py   MAX_RETRIES=3



### Docker Services│   └── llm_training_data.jsonl



```bash├── main.py                       # Main entry point```

# Start services

docker compose up -d├── docker-compose.yaml           # Docker services



# Stop services├── Makefile                      # DevOps commands   # Flaresolverr

docker compose down

├── requirements.txt              # Python dependencies

# View logs

docker compose logs -f├── .env.example                  # Example configuration### Check Keyword Database   FLARESOLVERR_ADDRESS=localhost



# Restart services└── README.md                     # This file

docker compose restart

``````   FLARESOLVERR_PORT=8191



### Ollama Management



```bash---```bash   ```

# Check if Qwen3:8b is installed

ollama list



# Pull model if missing## 🚀 Quick Startpython src/data/keywords.py

ollama pull qwen3:8b



# Test model

ollama run qwen3:8b "Test message"### Prerequisites```## Usage



# Remove model (frees 5.2GB)

ollama rm qwen3:8b

```- **Python 3.13+**



---- **Docker** & **Docker Compose**



## 📊 Analysis Details- **Ollama** (with Qwen3:8b model)## 📊 Analysis CapabilitiesRun flaresolverr locally with docker compose (supplied):



### Keyword Scoring (221+ Keywords)- **Discord Webhook** (optional, for alerts)



**Categories & Weights:**```bash

- 🔴 **CRITICAL** (weight: 20-30): War declarations, emergency tariffs

- 🟠 **HIGH** (weight: 15-20): Major tariffs, Fed actions, military deployments### Installation

- 🟡 **MEDIUM** (weight: 10-15): Policy discussions, regulatory changes

### 221+ Keywords covering:docker compose up -d

**Example Keywords:**

```python```bash

"tariff": 20,        # HIGH impact

"100% tariff": 30,   # CRITICAL impact# 1. Clone the repository- Trade policy (tariffs, quotas, sanctions)```

"massive tariff": 25,

"war": 30,git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git

"nuclear": 30,

"emergency": 25,cd YOUR-REPO-NAME- Monetary policy (Fed, interest rates)

"federal reserve": 20,

"bitcoin": 15,

"crypto regulation": 18

```# 2. Install Python dependencies- Cryptocurrency (Bitcoin, Ethereum, mining)Run the monitor:



### LLM Analysis (Qwen3:8b)pip install -r requirements.txt



**Configuration:**- Geopolitics (China, Russia, Iran)```bash

- **Model**: Qwen3:8b (5.2GB)

- **Temperature**: 0.1 (consistent scoring)# 3. Install Ollama (if not already installed)

- **Tokens**: 2000 max output

- **Timeout**: 60 seconds# macOS/Linux:- Tech regulation (antitrust, semiconductors)python main.py

- **Retries**: 3 attempts

curl https://ollama.ai/install.sh | sh

**Output Format:**

```json- Energy markets (OPEC, oil, gas)```

{

  "score": 90,# Windows:

  "reasoning": "Professional market analysis...",

  "urgency": "immediate",# Download from https://ollama.ai/download- Banking & finance

  "market_direction": {

    "stocks": "bearish",

    "crypto": "bearish",

    "forex": "usd_up",# 4. Pull Qwen3:8b model (5.2GB)Or using Docker:

    "commodities": "neutral"

  },ollama pull qwen3:8b

  "key_events": ["100% tariff on China"],

  "important_dates": ["November 1, 2025"]### Impact Levels```bash

}

```# 5. Start Docker services (MongoDB + FlareSolverr)



### Quality Check Systemdocker compose up -d- 🔴 **CRITICAL** (Score ≥50): Immediate market impactdocker build -t truth-social-monitor .



**Qwen3 Best Practices:**

- **Temperature**: 0.7

- **TopP**: 0.8# 6. Configure environment- 🟠 **HIGH** (Score 25-49): Significant relevancedocker run -d --env-file .env truth-social-monitor

- **TopK**: 20

- **enable_thinking**: False ⚠️ (critical for direct JSON)cp .env.example .env



**Checks:**# Edit .env with your settings (see Configuration section)- 🟡 **MEDIUM** (Score 10-24): Moderate impact```

1. ✅ Professional language

2. ✅ No internal jargon (no "75-89 range" mentions)

3. ✅ Clear market impact explanation

4. ✅ Factual accuracy# 7. Start the monitor- 🟢 **LOW** (Score <10): Minimal impact

5. ✅ Appropriate urgency

python main.py

**Example:**

```json## Configuration

{

  "approved": false,# Or using Make:

  "quality_score": 70,

  "issues_found": [make full-reset  # Complete reset + start## 🗺️ Roadmap

    "mentions internal scoring ranges"

  ],```

  "suggested_fixes": {

    "reasoning": "The 100% tariff will trigger..."All configuration is handled via environment variables, typically set in a `.env` file at the project root.

  }

}---

```

- [x] Fix keyword matching (whole words only)

---

## ⚙️ Configuration

## 🧪 Testing

- [x] Expand keyword database to 221+ keywords### Required Environment Variables

```bash

# Run all tests### Required Setup

python run_tests.py

- [ ] Ollama LLM Integration (In Progress)

# Test quality check

make test-quality-check1. **Create `.env` file** from `.env.example`:



# Test bad analysis examples   ```bash- [ ] Training data collection| Variable               | Description                                                      | Example/Default                |

python tests/test_bad_analysis.py

   cp .env.example .env

# Test LLM scenarios

python tests/test_llm_scenarios.py   ```- [ ] Custom spaCy NER model|------------------------|------------------------------------------------------------------|--------------------------------|

```



**Test Results:**

- ✅ Good analysis: 95/100 quality score, APPROVED2. **Configure Discord Webhook** (optional):- [ ] Hybrid analysis pipeline| `TRUTH_USERNAME`       | The Truth Social username to monitor                             | `realDonaldTrump`              |

- ❌ Bad analysis: 70/100 quality score, REJECTED with fixes

   - Go to Discord Server Settings

---

   - Integrations → Webhooks → New Webhook| `MONGO_DBSTRING`       | MongoDB connection string (URI)                                  | `mongodb+srv://...`            |

## 📈 Training Data

   - Copy webhook URL

All analyses are saved to `training_data/llm_training_data.jsonl`:

   - Paste into `.env`:---

```json

{     ```env

  "timestamp": "2025-10-11T18:30:00Z",

  "post_text": "...",     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN### Optional Environment Variables

  "keyword_score": 78,

  "llm_score": 90,     ```

  "llm_reasoning": "...",

  "urgency": "immediate",**⚠️ Disclaimer**: For informational purposes only. Not financial advice.

  "market_direction": {...},

  "quality_check": {3. **Key Settings** in `.env`:

    "approved": true,

    "quality_score": 95   ```env| Variable               | Description                                                      | Example/Default                |

  }

}   # Truth Social|------------------------|------------------------------------------------------------------|--------------------------------|

```

   TRUTH_USERNAME=realDonaldTrump| `LOG_FORMAT`           | Python logging format string                                     | See `config.py` for default    |

**Future Use:**

- spaCy NER training   | `LOG_LEVEL`            | Logging level                                                    | `INFO`                         |

- Model performance analysis

- Prompt improvement   # Ollama| `APPNAME`              | Application name                                                 | `Truth Social Monitor`         |



---   OLLAMA_MODEL=qwen3:8b| `ENV`                  | Environment name                                                 | `DEV`                          |



## 🛠️ Development   OLLAMA_URL=http://localhost:11434| `REPEAT_DELAY`         | Delay between checks (seconds)                                   | `300`                          |



### Make Commands   | `DISCORD_NOTIFY`       | Enable Discord notifications (`true`/`false`)                    | `true`                         |



```bash   # Discord (set to false to disable)| `DISCORD_USERNAME`     | Username for Discord bot                                         | `Truth Social Bot`             |

make help            # Show all commands

make restart         # Restart Docker   DISCORD_NOTIFY=true| `DISCORD_WEBHOOK_URL`  | Discord webhook URL                                              | *(required if notify enabled)* |

make clean-db        # Clear database

make full-reset      # Complete reset   DISCORD_WEBHOOK_URL=your_webhook_url| `MONGO_DB`             | MongoDB database name                                            | `truthsocial`                  |

make status          # Check services

make training-stats  # Training data info   | `MONGO_COLLECTION`     | MongoDB collection name                                          | `posts`                        |

```

   # Thresholds| `TRUTH_INSTANCE`       | Truth Social instance domain                                     | `truthsocial.com`              |

### Adding New Keywords

   LLM_THRESHOLD=20      # Minimum keyword score for LLM| `POST_TYPE`            | Type of posts to monitor                                         | `post`                         |

Edit `src/data/keywords.py`:

   DISCORD_THRESHOLD=25  # Minimum LLM score for alerts| `REQUEST_TIMEOUT`      | HTTP request timeout (seconds)                                   | `30`                           |

```python

KEYWORDS = {   | `MAX_RETRIES`          | Max HTTP request retries                                         | `3`                            |

    "your_keyword": 20,  # weight

    "another_keyword": 15,   # Quality Check (optional)| `FLARESOLVERR_ADDRESS` | Flaresolverr server address                                     | `localhost`                   |

    # ...

}   QUALITY_CHECK_ENABLED=true| `FLARESOLVERR_PORT`    | Flaresolverr server port                                        | `8191`                        |

```

   ```

### Modifying Prompts

### Example `.env` file

Edit files in `prompts/`:

- `market_analysis_prompt.py` - Main analysisSee `.env.example` for all available options.

- `quality_check_prompt.py` - QC validation

```env

---

---LOG_LEVEL=INFO

## 🔧 Troubleshooting

APPNAME="Truth Social Monitor"

### Ollama Connection Issues

## 📖 UsageENV=DEV

```bash

# Check if Ollama is runningREPEAT_DELAY=300

curl http://localhost:11434/api/tags

### Basic Commands

# Restart Ollama

# macOS/Linux:DISCORD_NOTIFY=true

ollama serve

```bashDISCORD_USERNAME="Truth Social Bot"

# Windows:

# Restart Ollama app# Start the monitorDISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

```

python main.py

### MongoDB Connection Issues

MONGO_DBSTRING=mongodb+srv://user:pass@host/db

```bash

# Check if MongoDB is running# Run with MakeMONGO_DB=truthsocial

docker ps | grep mongodb

make start           # Start applicationMONGO_COLLECTION=posts

# Restart MongoDB

docker compose restart mongodbmake full-reset      # Docker restart + DB clear + start

```

make test            # Run LLM test scenariosTRUTH_USERNAME=realDonaldTrump

### Quality Check Fails

make test-quality-check  # Test quality check systemTRUTH_INSTANCE=truthsocial.com

**Problem**: Empty responses or JSON parsing errors

make status          # Check all servicesPOST_TYPE=post

**Solution**: Ensure `enable_thinking=False` is set:

```pythonmake clean-db        # Clear MongoDB database

"options": {

    "enable_thinking": False,  # Critical for Qwen3!make training-stats  # Show training data statisticsREQUEST_TIMEOUT=30

    "temperature": 0.7,

    "top_p": 0.8,```MAX_RETRIES=3

    "top_k": 20

}

```

### Docker ServicesFLARESOLVERR_ADDRESS=localhost

---

FLARESOLVERR_PORT=8191

## 🚀 Repository Setup

```bash```

This project has been migrated from the original fork. Here's how to set up your own repository:

# Start services

### Clone & Setup

docker compose up -d### Validation

```bash

# Clone the repository

git clone git@github.com:Muslix/social-media-analyzer.git

cd social-media-analyzer/truthy# Stop services- If `DISCORD_NOTIFY` is `true`, `DISCORD_WEBHOOK_URL` **must** be set.



# Install dependenciesdocker compose down- `TRUTH_USERNAME` and `MONGO_DBSTRING` are always required.

pip install -r requirements.txt

```



### Migrate from Fork (if needed)# View logs---



```bashdocker compose logs -fFor more details, see the `config.py` file.

# Remove old remote

git remote remove origin



# Add your new repository# Restart services## Error Handling

git remote add origin git@github.com:Muslix/social-media-analyzer.git

docker compose restart

# Push to your repository

git push -u origin main```The application includes comprehensive error handling:

```

- Automatic retries for network failures

### Fresh Start (no history)

### Ollama Management- Rate limiting for Discord notifications

```bash

# Start fresh without old git history- Validation of configuration settings

rm -rf .git

git init```bash- Detailed logging of errors and operations

git add .

git commit -m "Initial commit: Trump Truth Social Market Analyzer"# Check if Qwen3:8b is installed- Safe storage of processed posts

git remote add origin git@github.com:Muslix/social-media-analyzer.git

git push -u origin mainollama list

```

## Contributing

---

# Pull model if missing

## 📚 Resources

ollama pull qwen3:8bFeel free to submit issues and pull requests.

- **Qwen3 Documentation**: https://huggingface.co/Qwen/Qwen3-8B

- **Ollama Documentation**: https://ollama.ai/docs

- **Docker Compose Guide**: https://docs.docker.com/compose/

- **MongoDB Setup**: https://www.mongodb.com/docs/# Test model## License



---ollama run qwen3:8b "Test message"



## 🗺️ RoadmapMIT License



- [x] Keyword matching with whole-word boundaries# Remove model (frees 5.2GB)

- [x] 221+ weighted keyword databaseollama rm qwen3:8b

- [x] Qwen3:8b LLM integration```

- [x] Quality check system

- [x] Market direction predictions---

- [x] Discord rich embeds

- [x] Training data collection## 📊 Analysis Details

- [ ] spaCy NER model training

- [ ] Hybrid pipeline (spaCy + LLM)### Keyword Scoring (221+ Keywords)

- [ ] Performance monitoring dashboard

- [ ] Web UI for analysis**Categories & Weights:**

- [ ] Multi-user support- 🔴 **CRITICAL** (weight: 20-30): War declarations, emergency tariffs

- 🟠 **HIGH** (weight: 15-20): Major tariffs, Fed actions, military deployments

---- 🟡 **MEDIUM** (weight: 10-15): Policy discussions, regulatory changes



## 🤝 Contributing**Example Keywords:**

```python

Contributions welcome! Please:"tariff": 20,        # HIGH impact

"100% tariff": 30,   # CRITICAL impact

1. Fork the repository"massive tariff": 25,

2. Create a feature branch"war": 30,

3. Make your changes"nuclear": 30,

4. Add tests if applicable"emergency": 25,

5. Submit a pull request"federal reserve": 20,

"bitcoin": 15,

---"crypto regulation": 18

```

## 📄 License

### LLM Analysis (Qwen3:8b)

MIT License - See LICENSE file for details

**Configuration:**

---- **Model**: Qwen3:8b (5.2GB)

- **Temperature**: 0.1 (consistent scoring)

## ⚠️ Disclaimer- **Tokens**: 2000 max output

- **Timeout**: 60 seconds

**This tool is for informational and educational purposes only.**- **Retries**: 3 attempts



- Not financial advice**Output Format:**

- Market analysis is AI-generated and may contain errors```json

- Always do your own research before making financial decisions{

- Past performance does not guarantee future results  "score": 90,

  "reasoning": "Professional market analysis...",

---  "urgency": "immediate",

  "market_direction": {

## 🙏 Credits    "stocks": "bearish",

    "crypto": "bearish",

Originally forked from [darrenwatt/truthy](https://github.com/darrenwatt/truthy), extensively rewritten with:    "forex": "usd_up",

- Complete LLM integration (Qwen3:8b)    "commodities": "neutral"

- Quality check system  },

- Market direction predictions  "key_events": ["100% tariff on China"],

- Professional prompt engineering  "important_dates": ["November 1, 2025"]

- Comprehensive testing suite}

```

---

### Quality Check System

**Built with ❤️ using Qwen3:8b, Python, and Docker**

**Qwen3 Best Practices:**

Repository: https://github.com/Muslix/social-media-analyzer- **Temperature**: 0.7

- **TopP**: 0.8
- **TopK**: 20
- **enable_thinking**: False ⚠️ (critical for direct JSON)

**Checks:**
1. ✅ Professional language
2. ✅ No internal jargon (no "75-89 range" mentions)
3. ✅ Clear market impact explanation
4. ✅ Factual accuracy
5. ✅ Appropriate urgency

**Example:**
```json
{
  "approved": false,
  "quality_score": 70,
  "issues_found": [
    "mentions internal scoring ranges"
  ],
  "suggested_fixes": {
    "reasoning": "The 100% tariff will trigger..."
  }
}
```

---

## 🧪 Testing

```bash
# Run all tests
python run_tests.py

# Test quality check
make test-quality-check

# Test bad analysis examples
python tests/test_bad_analysis.py

# Test LLM scenarios
python tests/test_llm_scenarios.py
```

**Test Results:**
- ✅ Good analysis: 95/100 quality score, APPROVED
- ❌ Bad analysis: 70/100 quality score, REJECTED with fixes

---

## 📈 Training Data

All analyses are saved to `training_data/llm_training_data.jsonl`:

```json
{
  "timestamp": "2025-10-11T18:30:00Z",
  "post_text": "...",
  "keyword_score": 78,
  "llm_score": 90,
  "llm_reasoning": "...",
  "urgency": "immediate",
  "market_direction": {...},
  "quality_check": {
    "approved": true,
    "quality_score": 95
  }
}
```

**Future Use:**
- spaCy NER training
- Model performance analysis
- Prompt improvement

---

## 🛠️ Development

### Make Commands

```bash
make help            # Show all commands
make restart         # Restart Docker
make clean-db        # Clear database
make full-reset      # Complete reset
make status          # Check services
make training-stats  # Training data info
```

### Adding New Keywords

Edit `src/data/keywords.py`:

```python
KEYWORDS = {
    "your_keyword": 20,  # weight
    "another_keyword": 15,
    # ...
}
```

### Modifying Prompts

Edit files in `prompts/`:
- `market_analysis_prompt.py` - Main analysis
- `quality_check_prompt.py` - QC validation

---

## 🔧 Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
# macOS/Linux:
ollama serve

# Windows:
# Restart Ollama app
```

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
docker ps | grep mongodb

# Restart MongoDB
docker compose restart mongodb
```

### Quality Check Fails

**Problem**: Empty responses or JSON parsing errors

**Solution**: Ensure `enable_thinking=False` is set:
```python
"options": {
    "enable_thinking": False,  # Critical for Qwen3!
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20
}
```

---

## 📚 Resources

- **Qwen3 Documentation**: https://huggingface.co/Qwen/Qwen3-8B
- **Ollama Documentation**: https://ollama.ai/docs
- **Docker Compose Guide**: https://docs.docker.com/compose/
- **MongoDB Setup**: https://www.mongodb.com/docs/

---

## 🗺️ Roadmap

- [x] Keyword matching with whole-word boundaries
- [x] 221+ weighted keyword database
- [x] Qwen3:8b LLM integration
- [x] Quality check system
- [x] Market direction predictions
- [x] Discord rich embeds
- [x] Training data collection
- [ ] spaCy NER model training
- [ ] Hybrid pipeline (spaCy + LLM)
- [ ] Performance monitoring dashboard
- [ ] Web UI for analysis
- [ ] Multi-user support

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## ⚠️ Disclaimer

**This tool is for informational and educational purposes only.**

- Not financial advice
- Market analysis is AI-generated and may contain errors
- Always do your own research before making financial decisions
- Past performance does not guarantee future results

---

## 🙏 Credits

Originally forked from [darrenwatt/truthy](https://github.com/darrenwatt/truthy), extensively rewritten with:
- Complete LLM integration (Qwen3:8b)
- Quality check system
- Market direction predictions
- Professional prompt engineering
- Comprehensive testing suite

---

**Built with ❤️ using Qwen3:8b, Python, and Docker**
