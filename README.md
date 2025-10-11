# 🤖 Truth Social Market Impact Analyzer

AI-powered real-time analysis of Truth Social posts for market impact prediction.

## What it does

- **Monitors** any Truth Social account (not just Trump - configurable via `TRUTH_USERNAME`)
- **Analyzes** posts using 221+ weighted keywords across trade, geopolitics, crypto, and markets
- **Predicts** market impact using Llama 3.2 3B LLM (CPU-optimized)
- **Sends** Discord alerts for high-impact posts with market direction predictions
- **Collects** training data for future ML improvements

## Features

- ✅ Keyword-based filtering (221+ keywords with whole-word matching)
- ✅ LLM analysis with Llama 3.2 3B (2GB, CPU-optimized)
- ✅ Quality checks to prevent bad analysis
- ✅ Market direction predictions (stocks, crypto, forex, commodities)
- ✅ Discord alerts with rich embeds
- ✅ Training data collection (JSONL format)
- ✅ Auto-restart via systemd service
- ✅ CPU thread optimization for faster inference

## Quick Start

```bash
# 1. Clone repository
git clone git@github.com:Muslix/social-media-analyzer.git
cd social-media-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Ollama + Llama 3.2 3B
curl https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b

# 4. Start Docker services (MongoDB + FlareSolverr)
docker compose up -d

# 5. Configure
cp .env.example .env
nano .env  # Edit with your settings

# 6. Run
python main.py
```

## Configuration

Required environment variables in `.env`:

```env
# Truth Social (works with any account!)
TRUTH_USERNAME=realDonaldTrump

# MongoDB
MONGO_DBSTRING=mongodb://localhost:27017/

# Discord (optional)
DISCORD_NOTIFY=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK

# Ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_NUM_THREADS=8  # Set to CPU core count (use 'nproc')
```

See `.env.example` for all options.

## Makefile Commands

```bash
make start              # Start application
make clean-db           # Clear MongoDB database
make full-reset         # Docker restart + DB clear + start
make status             # Check Docker services
make training-stats     # Show training data statistics
```

## Server Deployment (Auto-Restart)

The project includes systemd service configuration for production:

```bash
# On server - managed via systemd
./manage-service.sh start      # Start service
./manage-service.sh stop       # Stop service
./manage-service.sh restart    # Restart service
./manage-service.sh status     # Check status
./manage-service.sh logs       # Follow live logs
```

Service automatically:
- Starts on boot
- Restarts on crash (10s delay)
- Limits memory (2GB max)
- Logs to systemd journal

## How It Works

1. **Monitor** → Fetches new posts from configured Truth Social account
2. **Filter** → Analyzes with 221+ weighted keywords (whole-word matching)
3. **LLM Analysis** → If keyword score ≥ 20, runs Llama 3.2 3B analysis
4. **Quality Check** → Validates analysis quality before Discord
5. **Alert** → Sends Discord notification if LLM score ≥ 25
6. **Store** → Saves to MongoDB and training data (JSONL)

## Model Performance

| Model | Size | Speed (GPU) | Speed (CPU) | Quality | Use Case |
|-------|------|-------------|-------------|---------|----------|
| **Llama 3.2 3B** | 2GB | 4-5s | 15-30s | 90/100 | ✅ CPU servers (optimized) |
| Qwen3 8B | 5.2GB | 5-6s | 60-120s | 95/100 | GPU servers (best quality) |

**Recommendation:** 
- **CPU servers** → Use Llama 3.2 3B (2-4x faster on CPU, 61% less memory)
- **GPU servers** → Use Qwen3 8B if you need max quality (both are fast on GPU, ~5s)

## Roadmap

- [x] Keyword analysis with whole-word matching
- [x] LLM integration (Llama 3.2 3B)
- [x] Quality check system
- [x] Discord alerts with rich embeds
- [x] Training data collection
- [x] Systemd auto-restart service
- [ ] **Multi-account support** (monitor multiple Truth Social accounts)
- [ ] **Custom spaCy NER model** (train on collected data)
- [ ] **Hybrid pipeline** (spaCy NER + LLM fallback)
- [ ] **Performance monitoring dashboard**
- [ ] **Web UI** for configuration and monitoring
- [ ] **X/Twitter support** (expand beyond Truth Social)

## Tech Stack

- **Python 3.13+** - Core application
- **Ollama** - Local LLM inference (Llama 3.2 3B)
- **MongoDB** - Post storage and deduplication
- **FlareSolverr** - Cloudflare bypass (Docker)
- **Discord Webhooks** - Real-time alerts
- **systemd** - Service management and auto-restart

## License

MIT License - See LICENSE file

## Credits

Forked from [darrenwatt/truthy](https://github.com/darrenwatt/truthy) and extensively rewritten with:
- Llama 3.2 3B integration (CPU-optimized)
- Quality check system
- Market direction predictions
- Professional prompt engineering
- Systemd service management

---

**Repository:** [github.com/Muslix/social-media-analyzer](https://github.com/Muslix/social-media-analyzer)
