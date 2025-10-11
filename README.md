# 🤖 Trump Truth Social Market Impact Analyzer# 🤖 Trump Truth Social Market Impact Analyzer



AI-powered system that monitors Donald Trump's Truth Social posts and analyzes their potential market impact using **Qwen3:8b LLM** with intelligent quality checks.AI-powered system that monitors Donald Trump's Truth Social posts and analyzes their potential market impact using **Qwen3:8b LLM** with intelligent quality checks.



![Python](https://img.shields.io/badge/Python-3.13-blue)![Python](https://img.shields.io/badge/Python-3.13-blue)

![Qwen3](https://img.shields.io/badge/LLM-Qwen3--8B-green)![Qwen3](https://img.shields.io/badge/LLM-Qwen3--8B-green)

![Docker](https://img.shields.io/badge/Docker-Compose-blue)![Docker](https://img.shields.io/badge/Docker-Compose-blue)

![License](https://img.shields.io/badge/License-MIT-yellow)![License](https://img.shields.io/badge/License-MIT-yellow)



------



## 🎯 Features## 🎯 Features



### 🔍 **Multi-Layer Analysis Pipeline**### 🔍 **Multi-Layer Analysis Pipeline**

1. **Keyword Analysis** (221+ weighted keywords)1. **Keyword Analysis** (221+ weighted keywords)

   - Trade policy, tariffs, sanctions   - Trade policy, tariffs, sanctions

   - Monetary policy, Fed actions   - Monetary policy, Fed actions

   - Cryptocurrency regulations   - Cryptocurrency regulations

   - Geopolitics, military conflicts   - Geopolitics, military conflicts

   - Energy markets, commodities   - Energy markets, commodities



2. **LLM Analysis** (Qwen3:8b - 5.2GB model)2. **LLM Analysis** (Qwen3:8b - 5.2GB model)

   - Semantic understanding of market impact   - Semantic understanding of market impact

   - Score calibration (0-100)   - Score calibration (0-100)

   - Urgency classification (immediate/hours/days)   - Urgency classification (immediate/hours/days)

   - Market direction predictions (stocks/crypto/forex/commodities)   - Market direction predictions (stocks/crypto/forex/commodities)

   - Professional reasoning generation

   - Professional reasoning generation### 🔍 **Multi-Layer Analysis Pipeline**

3. **Quality Check** (Automated validation)

   - Validates analysis quality

   - Detects internal jargon

   - Suggests improvements3. **Quality Check** (Automated validation)1. **Keyword Analysis** (221+ weighted keywords)- **Multi-Layer Analysis**:- Forwards posts to Discord via webhooks

   - Ensures professional output

   - Validates analysis quality

### 📊 **Real-time Discord Alerts**

- Rich embeds with market analysis   - Detects internal jargon   - Trade policy, tariffs, sanctions

- German time formatting (CET/CEST)

- Color-coded urgency levels   - Suggests improvements

- Market direction indicators

- Direct links to original posts   - Ensures professional output   - Monetary policy, Fed actions  - 🔍 **Keyword Analysis**: 221+ weighted keywords across critical, high, and medium impact categories- Stores processed posts in MongoDB to avoid duplicates



### 💾 **Training Data Collection**

- Saves all analyses to JSONL format

- Includes quality check results### 📊 **Real-time Discord Alerts**   - Cryptocurrency regulations

- Ready for future spaCy NER training

- Tracks model performance- Rich embeds with market analysis



---- German time formatting (CET/CEST)   - Geopolitics, military conflicts  - 🤖 **LLM Analysis**: Ollama GPT-OSS:20B for intelligent semantic analysis (coming soon)- Supports media attachments (images, videos, GIFs)



## 🏗️ Architecture- Color-coded urgency levels



```- Market direction indicators   - Energy markets, commodities

┌─────────────────┐

│  Truth Social   │- Direct links to original posts

│   (via API)     │

└────────┬────────┘  - 🧠 **NER Model**: Custom spaCy model trained on market-specific entities (coming soon)- Rate limiting for Discord notifications

         │

         ▼### 💾 **Training Data Collection**

┌─────────────────┐

│  FlareSolverr   │ ← Cloudflare bypass- Saves all analyses to JSONL format2. **LLM Analysis** (Qwen3:8b - 5.2GB model)

│  (Docker)       │

└────────┬────────┘- Includes quality check results

         │

         ▼- Ready for future spaCy NER training   - Semantic understanding of market impact- **Smart Filtering**: Whole-word matching to avoid false positives- Automatic retries for failed requests

┌─────────────────┐

│ Keyword Filter  │ ← 221+ keywords- Tracks model performance

│  (Score 0-100)  │

└────────┬────────┘   - Score calibration (0-100)

         │

         ▼ (if score ≥ 20)---

┌─────────────────┐

│  Qwen3:8b LLM   │ ← Semantic analysis   - Urgency classification (immediate/hours/days)- **Impact Scoring**: Comprehensive scoring system with critical trigger detection- Comprehensive error handling and logging

│  (Ollama)       │

└────────┬────────┘## 🏗️ Architecture

         │

         ▼   - Market direction predictions (stocks/crypto/forex/commodities)

┌─────────────────┐

│ Quality Check   │ ← Validation```

│  (Qwen3:8b)     │

└────────┬────────┘┌─────────────────┐   - Professional reasoning generation- **Automated Alerts**: Three-tier output system (All Posts, High Impact, Critical Alerts)

         │

         ▼ (if score ≥ 25)│  Truth Social   │

┌─────────────────┐

│ Discord Alert   │ ← Rich embeds│   (via API)     │

└─────────────────┘

```└────────┬────────┘



---         │3. **Quality Check** (Automated validation)## Prerequisites



## 📁 Project Structure         ▼



```┌─────────────────┐   - Validates analysis quality

social-media-analyst/

├── src/│  FlareSolverr   │ ← Cloudflare bypass

│   ├── analyzers/

│   │   ├── market_analyzer.py    # Keyword-based analysis│  (Docker)       │   - Detects internal jargon## 📁 Project Structure

│   │   └── llm_analyzer.py       # Qwen3:8b LLM integration

│   ├── data/└────────┬────────┘

│   │   └── keywords.py           # 221+ weighted keywords

│   ├── output/         │   - Suggests improvements

│   │   ├── formatter.py          # Output formatting

│   │   └── discord_notifier.py   # Discord webhook integration         ▼

│   └── config.py                 # Configuration management

├── prompts/┌─────────────────┐   - Ensures professional output- Python 3.8 or higher

│   ├── market_analysis_prompt.py # Market analysis prompt

│   ├── quality_check_prompt.py   # Quality validation prompt│ Keyword Filter  │ ← 221+ keywords

│   ├── README.md                 # Prompt documentation

│   └── QUALITY_CHECK_SUMMARY.md  # QC system details│  (Score 0-100)  │

├── tests/

│   ├── test_quality_check.py     # QC tests└────────┬────────┘

│   ├── test_bad_analysis.py      # Negative tests

│   └── test_llm_scenarios.py     # LLM test scenarios         │### 📊 **Real-time Discord Alerts**```- MongoDB instance

├── output/                       # Generated output files

│   ├── truth_social_posts.txt         ▼ (if score ≥ 20)

│   ├── market_impact_posts.txt

│   └── CRITICAL_ALERTS.txt┌─────────────────┐- Rich embeds with market analysis

├── training_data/                # ML training data

│   └── llm_training_data.jsonl│  Qwen3:8b LLM   │ ← Semantic analysis

├── main.py                       # Main entry point

├── docker-compose.yaml           # Docker services│  (Ollama)       │- German time formatting (CET/CEST)truthy/- Discord webhook URL

├── Makefile                      # DevOps commands

├── requirements.txt              # Python dependencies└────────┬────────┘

├── .env.example                  # Example configuration

└── README.md                     # This file         │- Color-coded urgency levels

```

         ▼

---

┌─────────────────┐- Market direction indicators├── src/                          # Source code- Flaresolverr to run requests through

## 🚀 Quick Start

│ Quality Check   │ ← Validation

### Prerequisites

│  (Qwen3:8b)     │- Direct links to original posts

- **Python 3.13+**

- **Docker** & **Docker Compose**└────────┬────────┘

- **Ollama** (with Qwen3:8b model)

- **Discord Webhook** (optional, for alerts)         ││   ├── analyzers/                # Analysis modules



### Installation         ▼ (if score ≥ 25)



```bash┌─────────────────┐### 💾 **Training Data Collection**

# 1. Clone the repository

git clone git@github.com:Muslix/social-media-analyzer.git│ Discord Alert   │ ← Rich embeds

cd social-media-analyzer

└─────────────────┘- Saves all analyses to JSONL format│   │   ├── market_analyzer.py    # Keyword-based market analysis## Installation

# 2. Install Python dependencies

pip install -r requirements.txt```



# 3. Install Ollama (if not already installed)- Includes quality check results

# macOS/Linux:

curl https://ollama.ai/install.sh | sh---



# Windows:- Ready for future spaCy NER training│   │   └── llm_analyzer.py       # Ollama LLM analysis (coming soon)

# Download from https://ollama.ai/download

## 📁 Project Structure

# 4. Pull Qwen3:8b model (5.2GB)

ollama pull qwen3:8b- Tracks model performance



# 5. Start Docker services (MongoDB + FlareSolverr)```

docker compose up -d

truthy/│   ├── data/                     # Data & configuration1. Clone the repository:

# 6. Configure environment

cp .env.example .env├── src/

# Edit .env with your settings (see Configuration section)

│   ├── analyzers/---

# 7. Start the monitor

python main.py│   │   ├── market_analyzer.py    # Keyword-based analysis



# Or using Make:│   │   └── llm_analyzer.py       # Qwen3:8b LLM integration│   │   └── keywords.py           # Comprehensive keyword database (221+ keywords)   ```bash

make full-reset  # Complete reset + start

```│   ├── data/



---│   │   └── keywords.py           # 221+ weighted keywords## 🏗️ Architecture



## ⚙️ Configuration│   ├── output/



### Required Setup│   │   ├── formatter.py          # Output formatting│   ├── output/                   # Output formatting   git clone https://github.com/darrenwatt/truthy.git



1. **Create `.env` file** from `.env.example`:│   │   └── discord_notifier.py   # Discord webhook integration

   ```bash

   cp .env.example .env│   └── config.py                 # Configuration management```

   ```

├── prompts/

2. **Configure Discord Webhook** (optional):

   - Go to Discord Server Settings│   ├── market_analysis_prompt.py # Market analysis prompt┌─────────────────┐│   │   └── formatter.py          # Result formatting and file output   cd truthy

   - Integrations → Webhooks → New Webhook

   - Copy webhook URL│   ├── quality_check_prompt.py   # Quality validation prompt

   - Paste into `.env`:

     ```env│   ├── README.md                 # Prompt documentation│  Truth Social   │

     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN

     ```│   └── QUALITY_CHECK_SUMMARY.md  # QC system details



3. **Key Settings** in `.env`:├── tests/│   (via API)     ││   └── config.py                 # Application configuration   ```

   ```env

   # Truth Social│   ├── test_quality_check.py     # QC tests

   TRUTH_USERNAME=realDonaldTrump

   │   ├── test_bad_analysis.py      # Negative tests└────────┬────────┘

   # Ollama

   OLLAMA_MODEL=qwen3:8b│   └── test_llm_scenarios.py     # LLM test scenarios

   OLLAMA_URL=http://localhost:11434

   ├── output/                       # Generated output files         │├── tests/                        # Test suite

   # Discord (set to false to disable)

   DISCORD_NOTIFY=true│   ├── truth_social_posts.txt

   DISCORD_WEBHOOK_URL=your_webhook_url

   │   ├── market_impact_posts.txt         ▼

   # Thresholds

   LLM_THRESHOLD=20      # Minimum keyword score for LLM│   └── CRITICAL_ALERTS.txt

   DISCORD_THRESHOLD=25  # Minimum LLM score for alerts

   ├── training_data/                # ML training data┌─────────────────┐│   ├── test_whole_word_matching.py2. Install dependencies:

   # Quality Check (optional)

   QUALITY_CHECK_ENABLED=true│   └── llm_training_data.jsonl

   ```

├── main.py                       # Main entry point│  FlareSolverr   │ ← Cloudflare bypass

See `.env.example` for all available options.

├── docker-compose.yaml           # Docker services

---

├── Makefile                      # DevOps commands│  (Docker)       ││   └── test_expanded_keywords.py   ```bash

## 📖 Usage

├── requirements.txt              # Python dependencies

### Basic Commands

├── .env.example                  # Example configuration└────────┬────────┘

```bash

# Start the monitor└── README.md                     # This file

python main.py

```         │├── scripts/                      # Utility scripts   pip install -r requirements.txt

# Run with Make

make start           # Start application

make full-reset      # Docker restart + DB clear + start

make test            # Run LLM test scenarios---         ▼

make test-quality-check  # Test quality check system

make status          # Check all services

make clean-db        # Clear MongoDB database

make training-stats  # Show training data statistics## 🚀 Quick Start┌─────────────────┐│   ├── analyze_posts.py          # One-time analysis   ```

```



### Docker Services

### Prerequisites│ Keyword Filter  │ ← 221+ keywords

```bash

# Start services

docker compose up -d

- **Python 3.13+**│  (Score 0-100)  ││   └── deep_analysis.py          # Deep historical analysis

# Stop services

docker compose down- **Docker** & **Docker Compose**



# View logs- **Ollama** (with Qwen3:8b model)└────────┬────────┘

docker compose logs -f

- **Discord Webhook** (optional, for alerts)

# Restart services

docker compose restart         │├── output/                       # Generated output files3. Create a `.env` file with your configuration:

```

### Installation

### Ollama Management

         ▼ (if score ≥ 20)

```bash

# Check if Qwen3:8b is installed```bash

ollama list

# 1. Clone the repository┌─────────────────┐│   ├── truth_social_posts.txt   ```env

# Pull model if missing

ollama pull qwen3:8bgit clone git@github.com:Muslix/social-media-analyzer.git



# Test modelcd social-media-analyzer/truthy│  Qwen3:8b LLM   │ ← Semantic analysis

ollama run qwen3:8b "Test message"



# Remove model (frees 5.2GB)

ollama rm qwen3:8b# 2. Install Python dependencies│  (Ollama)       ││   ├── market_impact_posts.txt   # Logging

```

pip install -r requirements.txt

---

└────────┬────────┘

## 📊 Analysis Details

# 3. Install Ollama (if not already installed)

### Keyword Scoring (221+ Keywords)

# macOS/Linux:         ││   └── CRITICAL_ALERTS.txt   LOG_LEVEL=INFO

**Categories & Weights:**

- 🔴 **CRITICAL** (weight: 20-30): War declarations, emergency tariffscurl https://ollama.ai/install.sh | sh

- 🟠 **HIGH** (weight: 15-20): Major tariffs, Fed actions, military deployments

- 🟡 **MEDIUM** (weight: 10-15): Policy discussions, regulatory changes         ▼



**Example Keywords:**# Windows:

```python

"tariff": 20,        # HIGH impact# Download from https://ollama.ai/download┌─────────────────┐├── training_data/                # ML training data storage   APPNAME="Truth Social Monitor"

"100% tariff": 30,   # CRITICAL impact

"massive tariff": 25,

"war": 30,

"nuclear": 30,# 4. Pull Qwen3:8b model (5.2GB)│ Quality Check   │ ← Validation

"emergency": 25,

"federal reserve": 20,ollama pull qwen3:8b

"bitcoin": 15,

"crypto regulation": 18│  (Qwen3:8b)     │├── main.py                       # Main entry point   ENV=PROD

```

# 5. Start Docker services (MongoDB + FlareSolverr)

### LLM Analysis (Qwen3:8b)

docker compose up -d└────────┬────────┘

**Configuration:**

- **Model**: Qwen3:8b (5.2GB)

- **Temperature**: 0.1 (consistent scoring)

- **Tokens**: 2000 max output# 6. Configure environment         │├── run_tests.py                  # Test runner   REPEAT_DELAY=300

- **Timeout**: 60 seconds

- **Retries**: 3 attemptscp .env.example .env



**Output Format:**# Edit .env with your settings (see Configuration section)         ▼ (if score ≥ 25)

```json

{

  "score": 90,

  "reasoning": "Professional market analysis...",# 7. Start the monitor┌─────────────────┐├── docker-compose.yaml           # Docker services (MongoDB, FlareSolverr)

  "urgency": "immediate",

  "market_direction": {python main.py

    "stocks": "bearish",

    "crypto": "bearish",│ Discord Alert   │ ← Rich embeds

    "forex": "usd_up",

    "commodities": "neutral"# Or using Make:

  },

  "key_events": ["100% tariff on China"],make full-reset  # Complete reset + start└─────────────────┘├── requirements.txt              # Python dependencies   # Discord

  "important_dates": ["November 1, 2025"]

}```

```

```

### Quality Check System

---

**Qwen3 Best Practices:**

- **Temperature**: 0.7└── .env                          # Environment configuration   DISCORD_NOTIFY=true

- **TopP**: 0.8

- **TopK**: 20## ⚙️ Configuration

- **enable_thinking**: False ⚠️ (critical for direct JSON)

---

**Checks:**

1. ✅ Professional language### Required Setup

2. ✅ No internal jargon (no "75-89 range" mentions)

3. ✅ Clear market impact explanation```   DISCORD_USERNAME="Truth Social Bot"

4. ✅ Factual accuracy

5. ✅ Appropriate urgency1. **Create `.env` file** from `.env.example`:



**Example:**   ```bash## 📁 Project Structure

```json

{   cp .env.example .env

  "approved": false,

  "quality_score": 70,   ```   DISCORD_WEBHOOK_URL=your_webhook_url_here

  "issues_found": [

    "mentions internal scoring ranges"

  ],

  "suggested_fixes": {2. **Configure Discord Webhook** (optional):```

    "reasoning": "The 100% tariff will trigger..."

  }   - Go to Discord Server Settings

}

```   - Integrations → Webhooks → New Webhooktruthy/## 🛠️ Setup & Usage



---   - Copy webhook URL



## 🧪 Testing   - Paste into `.env`:├── src/



```bash     ```env

# Run all tests

python run_tests.py     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN│   ├── analyzers/   # MongoDB



# Test quality check     ```

make test-quality-check

│   │   ├── market_analyzer.py    # Keyword-based analysis

# Test bad analysis examples

python tests/test_bad_analysis.py3. **Key Settings** in `.env`:



# Test LLM scenarios   ```env│   │   └── llm_analyzer.py       # Qwen3:8b LLM integration### Quick Start   MONGO_DBSTRING=mongodb://localhost:27017/

python tests/test_llm_scenarios.py

```   # Truth Social



**Test Results:**   TRUTH_USERNAME=realDonaldTrump│   ├── data/

- ✅ Good analysis: 95/100 quality score, APPROVED

- ❌ Bad analysis: 70/100 quality score, REJECTED with fixes   



---   # Ollama│   │   └── keywords.py           # 221+ weighted keywords   MONGO_DB=truthsocial



## 📈 Training Data   OLLAMA_MODEL=qwen3:8b



All analyses are saved to `training_data/llm_training_data.jsonl`:   OLLAMA_URL=http://localhost:11434│   ├── output/



```json   

{

  "timestamp": "2025-10-11T18:30:00Z",   # Discord (set to false to disable)│   │   ├── formatter.py          # Output formatting```bash   MONGO_COLLECTION=posts

  "post_text": "...",

  "keyword_score": 78,   DISCORD_NOTIFY=true

  "llm_score": 90,

  "llm_reasoning": "...",   DISCORD_WEBHOOK_URL=your_webhook_url│   │   └── discord_notifier.py   # Discord webhook integration

  "urgency": "immediate",

  "market_direction": {...},   

  "quality_check": {

    "approved": true,   # Thresholds│   └── config.py                 # Configuration management# Start Docker services

    "quality_score": 95

  }   LLM_THRESHOLD=20      # Minimum keyword score for LLM

}

```   DISCORD_THRESHOLD=25  # Minimum LLM score for alerts├── prompts/



**Future Use:**   

- spaCy NER training

- Model performance analysis   # Quality Check (optional)│   ├── market_analysis_prompt.py # Market analysis promptdocker-compose up -d   # Truth Social

- Prompt improvement

   QUALITY_CHECK_ENABLED=true

---

   ```│   ├── quality_check_prompt.py   # Quality validation prompt

## 🛠️ Development



### Make Commands

See `.env.example` for all available options.│   ├── README.md                 # Prompt documentation   TRUTH_USERNAME=username_to_monitor

```bash

make help            # Show all commands

make restart         # Restart Docker

make clean-db        # Clear database---│   └── QUALITY_CHECK_SUMMARY.md  # QC system details

make full-reset      # Complete reset

make status          # Check services

make training-stats  # Training data info

```## 📖 Usage├── tests/# Run the monitor   TRUTH_INSTANCE=truthsocial.com



### Adding New Keywords



Edit `src/data/keywords.py`:### Basic Commands│   ├── test_quality_check.py     # QC tests



```python

KEYWORDS = {

    "your_keyword": 20,  # weight```bash│   ├── test_bad_analysis.py      # Negative testspython main.py

    "another_keyword": 15,

    # ...# Start the monitor

}

```python main.py│   └── test_llm_scenarios.py     # LLM test scenarios



### Modifying Prompts



Edit files in `prompts/`:# Run with Make├── output/                       # Generated output files   # Request Settings

- `market_analysis_prompt.py` - Main analysis

- `quality_check_prompt.py` - QC validationmake start           # Start application



---make full-reset      # Docker restart + DB clear + start│   ├── truth_social_posts.txt



## 🔧 Troubleshootingmake test            # Run LLM test scenarios



### Ollama Connection Issuesmake test-quality-check  # Test quality check system│   ├── market_impact_posts.txt# Run tests   REQUEST_TIMEOUT=30



```bashmake status          # Check all services

# Check if Ollama is running

curl http://localhost:11434/api/tagsmake clean-db        # Clear MongoDB database│   └── CRITICAL_ALERTS.txt



# Restart Ollamamake training-stats  # Show training data statistics

# macOS/Linux:

ollama serve```├── training_data/                # ML training datapython run_tests.py   MAX_RETRIES=3



# Windows:

# Restart Ollama app

```### Docker Services│   └── llm_training_data.jsonl



### MongoDB Connection Issues



```bash```bash├── main.py                       # Main entry point```

# Check if MongoDB is running

docker ps | grep mongodb# Start services



# Restart MongoDBdocker compose up -d├── docker-compose.yaml           # Docker services

docker compose restart mongodb

```



### Quality Check Fails# Stop services├── Makefile                      # DevOps commands   # Flaresolverr



**Problem**: Empty responses or JSON parsing errorsdocker compose down



**Solution**: Ensure `enable_thinking=False` is set:├── requirements.txt              # Python dependencies

```python

"options": {# View logs

    "enable_thinking": False,  # Critical for Qwen3!

    "temperature": 0.7,docker compose logs -f├── .env.example                  # Example configuration### Check Keyword Database   FLARESOLVERR_ADDRESS=localhost

    "top_p": 0.8,

    "top_k": 20

}

```# Restart services└── README.md                     # This file



---docker compose restart



## 🚀 Repository Setup``````   FLARESOLVERR_PORT=8191



This project has been migrated from the original fork. Here's how to set up your own repository:



### Clone & Setup### Ollama Management



```bash

# Clone the repository

git clone git@github.com:Muslix/social-media-analyzer.git```bash---```bash   ```

cd social-media-analyzer

# Check if Qwen3:8b is installed

# Install dependencies

pip install -r requirements.txtollama list

```



### Migrate from Fork (if needed)

# Pull model if missing## 🚀 Quick Startpython src/data/keywords.py

```bash

# Remove old remoteollama pull qwen3:8b

git remote remove origin



# Add your new repository

git remote add origin git@github.com:Muslix/social-media-analyzer.git# Test model



# Push to your repositoryollama run qwen3:8b "Test message"### Prerequisites```## Usage

git push -u origin main

```



### Fresh Start (no history)# Remove model (frees 5.2GB)



```bashollama rm qwen3:8b

# Start fresh without old git history

rm -rf .git```- **Python 3.13+**

git init

git add .

git commit -m "Initial commit: Trump Truth Social Market Analyzer"

git remote add origin git@github.com:Muslix/social-media-analyzer.git---- **Docker** & **Docker Compose**

git push -u origin main

```



---## 📊 Analysis Details- **Ollama** (with Qwen3:8b model)## 📊 Analysis CapabilitiesRun flaresolverr locally with docker compose (supplied):



## 📚 Resources



- **Qwen3 Documentation**: https://huggingface.co/Qwen/Qwen3-8B### Keyword Scoring (221+ Keywords)- **Discord Webhook** (optional, for alerts)

- **Ollama Documentation**: https://ollama.ai/docs

- **Docker Compose Guide**: https://docs.docker.com/compose/

- **MongoDB Setup**: https://www.mongodb.com/docs/

**Categories & Weights:**```bash

---

- 🔴 **CRITICAL** (weight: 20-30): War declarations, emergency tariffs

## 🗺️ Roadmap

- 🟠 **HIGH** (weight: 15-20): Major tariffs, Fed actions, military deployments### Installation

- [x] Keyword matching with whole-word boundaries

- [x] 221+ weighted keyword database- 🟡 **MEDIUM** (weight: 10-15): Policy discussions, regulatory changes

- [x] Qwen3:8b LLM integration

- [x] Quality check system### 221+ Keywords covering:docker compose up -d

- [x] Market direction predictions

- [x] Discord rich embeds**Example Keywords:**

- [x] Training data collection

- [ ] spaCy NER model training```python```bash

- [ ] Hybrid pipeline (spaCy + LLM)

- [ ] Performance monitoring dashboard"tariff": 20,        # HIGH impact

- [ ] Web UI for analysis

- [ ] Multi-user support"100% tariff": 30,   # CRITICAL impact# 1. Clone the repository- Trade policy (tariffs, quotas, sanctions)```



---"massive tariff": 25,



## 🤝 Contributing"war": 30,git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git



Contributions welcome! Please:"nuclear": 30,



1. Fork the repository"emergency": 25,cd YOUR-REPO-NAME- Monetary policy (Fed, interest rates)

2. Create a feature branch

3. Make your changes"federal reserve": 20,

4. Add tests if applicable

5. Submit a pull request"bitcoin": 15,



---"crypto regulation": 18



## 📄 License```# 2. Install Python dependencies- Cryptocurrency (Bitcoin, Ethereum, mining)Run the monitor:



MIT License - See LICENSE file for details



---### LLM Analysis (Qwen3:8b)pip install -r requirements.txt



## ⚠️ Disclaimer



**This tool is for informational and educational purposes only.****Configuration:**- Geopolitics (China, Russia, Iran)```bash



- Not financial advice- **Model**: Qwen3:8b (5.2GB)

- Market analysis is AI-generated and may contain errors

- Always do your own research before making financial decisions- **Temperature**: 0.1 (consistent scoring)# 3. Install Ollama (if not already installed)

- Past performance does not guarantee future results

- **Tokens**: 2000 max output

---

- **Timeout**: 60 seconds# macOS/Linux:- Tech regulation (antitrust, semiconductors)python main.py

## 🙏 Credits

- **Retries**: 3 attempts

Originally forked from [darrenwatt/truthy](https://github.com/darrenwatt/truthy), extensively rewritten with:

- Complete LLM integration (Qwen3:8b)curl https://ollama.ai/install.sh | sh

- Quality check system

- Market direction predictions**Output Format:**

- Professional prompt engineering

- Comprehensive testing suite```json- Energy markets (OPEC, oil, gas)```



---{



**Built with ❤️ using Qwen3:8b, Python, and Docker**  "score": 90,# Windows:



Repository: https://github.com/Muslix/social-media-analyzer  "reasoning": "Professional market analysis...",


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
