┌─────────────────────────────────────────────────┐
│  Phase 1: QUICK WINS (Jetzt sofort)            │
├─────────────────────────────────────────────────┤
│  ✓ Fix Whole-Word Matching (\b boundaries)     │
│  ✓ Erweitere Keywords massiv (hunderte)        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Phase 2: LLM INTEGRATION (Diese Woche)        │
├─────────────────────────────────────────────────┤
│  ✓ Ollama GPT-OSS:20B anbinden                 │
│  ✓ Smart Prompts für Market Analysis           │
│  ✓ Vorfilterung: Keyword Score > 20            │
│  ✓ Training-Daten sammeln (JSON logs)          │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Phase 3: ML TRAINING (Nach ~1000 Posts)       │
├─────────────────────────────────────────────────┤
│  ✓ Custom spaCy NER trainieren                 │
│  ✓ Entities: TARIFF_ACTION, POLICY_CHANGE...   │
│  ✓ Ollama-Analysen als Ground Truth            │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Phase 4: PRODUCTION (Finale Pipeline)         │
├─────────────────────────────────────────────────┤
│  Keywords → spaCy NER → Ollama (Fallback)      │
│  Schnell, präzise, kosteneffizient!            │
└─────────────────────────────────────────────────┘