# 🤖 Social Media Market Impact Analyzer

AI-powered real-time analysis of social media posts for market impact prediction.

## What it does

- **Monitors** any Truth Social account + X/Twitter accounts (pre-configured market-moving accounts)
- **Tracks** high-impact influencers: Elon Musk, Bill Ackman, Michael Saylor, Cathie Wood, and more
- **Analyzes** posts using 221+ weighted keywords across trade, geopolitics, crypto, and markets
- **Predicts** market impact using Llama 3.2 3B LLM (CPU-optimized)
- **Sends** Discord alerts for high-impact posts with market direction predictions
- **Collects** training data for future ML improvements
- **Multi-Platform** support with automatic instance rotation (Nitter for X/Twitter)

## Features

- ✅ **Multi-Platform**: Truth Social + X/Twitter monitoring
- ✅ **Multi-User Tracking**: Monitor multiple high-impact accounts simultaneously
- ✅ **Market Influencers**: Pre-configured list of proven market-moving accounts
- ✅ **Nitter Scraping**: No X API key needed, automatic instance rotation
- ✅ **No Cloudflare Bypass**: Direct API access only (legally safer)
- ✅ Keyword-based filtering (221+ keywords with whole-word matching)
- ✅ LLM analysis with Llama 3.2 3B (2GB, CPU-optimized)
- ✅ Quality checks to prevent bad analysis
- ✅ Market direction predictions (stocks, crypto, forex, commodities)
- ✅ Discord alerts with rich embeds
- ✅ Training data collection (JSONL format)
- ✅ Auto-restart via systemd service
- ✅ CPU thread optimization for faster inference

## ⚠️ Legal Notice

**READ BEFORE USE:** This tool scrapes publicly available social media data. You are **solely responsible** for ensuring your use complies with:
- Platform Terms of Service (X/Twitter, Truth Social)  
- Local and international laws  
- Data protection regulations (GDPR, CCPA, etc.)

📄 **See [DISCLAIMER.md](DISCLAIMER.md) for full legal information**

This tool is for **educational/research purposes only**. For commercial use:
- ✅ Consult a lawyer
- ✅ Use official APIs (X API for Twitter)
- ✅ Obtain proper authorization

### 🛡️ Legal Improvements (v2.0)

**FlareSolverr has been removed** to improve legal compliance:
- ✅ **No active Cloudflare bypass** (previously used FlareSolverr)
- ✅ **Direct API access only** for Truth Social
- ✅ **Nitter for X/Twitter** (uses public instances)
- ✅ **Proper rate limiting** and respectful scraping
- ⚠️ **Truth Social may not work** if Cloudflare is enabled

**Recommendation:** Focus on X/Twitter monitoring (6 high-impact accounts: Musk, Ackman, Saylor, Wood, Chamath, Pomp)

📚 **See [docs/FLARESOLVERR_REMOVAL.md](docs/FLARESOLVERR_REMOVAL.md)** for migration details

Web scraping may violate platform ToS and could result in:
- IP blocking
- Cease-and-desist notices
- Legal action

**Proceed at your own risk.**

## Quick Start

```bash
# 1. Clone repository
git clone git@github.com:Muslix/social-media-analyzer.git
cd social-media-analyzer

# 2. READ THE DISCLAIMER
cat DISCLAIMER.md  # ⚠️ IMPORTANT - Read carefully!

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Ollama + Llama 3.2 3B
curl https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b

# 4. Start Docker services (app + FlareSolverr + MongoDB)
docker compose up -d

# 5. Watch logs / accept disclaimer
docker compose logs -f app

# 6. Configure (if running locally instead of Docker)
cp .env.example .env
nano .env  # Edit with your settings

# 7. Run locally (optional alternative to Docker)
python main.py
```

## Configuration

Required environment variables in `.env`:

```env
# Truth Social Account (optional - configure any account to monitor)
TRUTH_USERNAME=your_account_to_monitor

# X/Twitter Accounts (optional - via Nitter scraping, no API key needed)
X_ENABLED=true
# Pre-configured high-impact market-moving accounts:
# - @elonmusk: Tesla CEO, crypto influencer (Bitcoin, Dogecoin)
# - @BillAckman: Activist investor, macro trades
# - @michael_saylor: MicroStrategy CEO, Bitcoin advocate
# - @CathieDWood: ARK Invest CEO, growth stocks
# - @chamath: Venture capitalist, SPACs, crypto
# - @APompliano: Bitcoin podcaster, crypto advocate
X_USERNAMES=elonmusk,BillAckman,michael_saylor,CathieDWood,chamath,APompliano

# MongoDB
MONGO_DBSTRING=mongodb://mongodb:27017/
# (Use mongodb://localhost:27017/ when running everything on the host)

# Adaptive polling interval (defaults to 10 minutes if min/max omitted)
REPEAT_DELAY=600
REPEAT_MIN_DELAY=420
REPEAT_MAX_DELAY=840
BLOCKED_BACKOFF_MIN=900
BLOCKED_BACKOFF_MAX=1500
EMPTY_FETCH_THRESHOLD=3
EMPTY_FETCH_BACKOFF_MULTIPLIER=1.5

# FlareSolverr (enables Cloudflare-friendly requests)
FLARESOLVERR_ENABLED=true
FLARESOLVERR_URL=http://flaresolverr:8191

# Discord (optional)
DISCORD_NOTIFY=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK

# Ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_NUM_THREADS=8  # Set to CPU core count (use 'nproc')
```

**Note:** Either Truth Social (`TRUTH_USERNAMES`) OR X/Twitter (`X_ENABLED=true`) must be configured. You can enable both for multi-platform monitoring. Each platform supports **multiple accounts** (comma-separated).

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

1. **Monitor** → Fetches new posts every **10 minutes** from configured social media accounts
2. **Filter** → Analyzes with 221+ weighted keywords (whole-word matching)
3. **LLM Analysis** → If keyword score ≥ 20, runs Llama 3.2 3B analysis
4. **Quality Check** → Validates analysis quality before Discord
5. **Alert** → Sends Discord notification if LLM score ≥ 25
6. **Store** → Saves to MongoDB and training data (JSONL)

**Tracked Accounts (X/Twitter):**
- 🚗 **Elon Musk** (@elonmusk) - Tesla, crypto, markets
- 💼 **Bill Ackman** (@BillAckman) - Activist investor, macro
- ₿ **Michael Saylor** (@michael_saylor) - Bitcoin advocate
- 📈 **Cathie Wood** (@CathieDWood) - ARK Invest, growth stocks
- 🚀 **Chamath** (@chamath) - VC, SPACs, crypto
- 🎙️ **Pomp** (@APompliano) - Bitcoin influencer

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
- [x] **X/Twitter integration** (via Nitter scraping with instance rotation)
- [x] **Multi-platform monitoring** (Truth Social + X/Twitter simultaneously)
- [x] **Multi-user tracking** (6 pre-configured market-moving accounts)
- [x] **10-minute intervals** (optimized for rate limits and server load)
- [x] **FlareSolverr removal** (improved legal compliance - no active Cloudflare bypass)
- [x] **Legal disclaimer system** (user consent and documentation)
- [ ] **Custom account lists** (easy configuration for any X/Twitter accounts)
- [ ] **Official X API support** (option for legally compliant commercial use)
- [ ] **Custom spaCy NER model** (train on collected data)
- [ ] **Hybrid pipeline** (spaCy NER + LLM fallback)
- [ ] **Performance monitoring dashboard**
- [ ] **Web UI** for configuration and monitoring
- [ ] **Additional platforms** (Mastodon, Bluesky support)

## Tech Stack

- **Python 3.13+** - Core application
- **Ollama** - Local LLM inference (Llama 3.2 3B)
- **MongoDB** - Post storage and deduplication
- **Nitter** - X/Twitter scraping (public instances)
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
