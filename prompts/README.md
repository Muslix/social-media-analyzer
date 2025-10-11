# LLM Prompts Documentation

Dieses Verzeichnis enthält alle LLM-Prompts für die Trump Truth Social Analyse.

## Struktur

### 1. Market Analysis Prompt (`market_analysis_prompt.py`)
**Zweck**: Erste Stufe der Analyse - bewertet Market Impact eines Posts

**Eingabe**:
- Post Text

**Ausgabe** (JSON):
```json
{
  "score": 0-100,
  "reasoning": "Professional market analysis",
  "affected_markets": {...},
  "key_events": [...],
  "important_dates": [...],
  "urgency": "immediate|hours|days"
}
```

**Scoring Guidelines**:
- 90-100: Konkrete Zahlen (100% Tariff, $50B Deal)
- 75-89: Vage Aussagen ("massive tariffs", "large scale")
- 60-74: Kleine Tariffs oder Regulatory Changes
- 25-49: Policy Diskussionen
- 0-24: Minimal relevante Aussagen

**Key Features**:
- ✅ Separiert Guidelines (für AI Referenz) von Reasoning Output
- ✅ Explizite Anti-Pattern Instructions ("DO NOT mention score ranges")
- ✅ Beispiele für gutes vs schlechtes Reasoning
- ✅ Fokus auf professionelle Market Analyse (WHAT + WHY)

---

### 2. Quality Check Prompt (`quality_check_prompt.py`)
**Zweck**: Zweite Stufe - validiert ob die Analyse Discord-ready ist

**Eingabe**:
- Original Post Text
- Proposed Analysis (Score, Reasoning, Urgency, Market Impact)

**Ausgabe** (JSON):
```json
{
  "approved": true/false,
  "issues_found": ["issue1", "issue2"],
  "suggested_fixes": {
    "reasoning": "improved text or null",
    "urgency": "corrected value or null", 
    "score": 85
  },
  "quality_score": 0-100
}
```

**Quality Criteria**:
1. ✅ Professional Language (klingt wie Market Analyst)
2. ✅ No Internal Jargon (keine "75-89 range" Mentions)
3. ✅ Clear Market Impact (WHAT + WHY erklärt)
4. ✅ Factual Accuracy (basiert auf Post Content)
5. ✅ Appropriate Urgency (matched konkrete Aktionen)

**Verhindert**:
- ❌ "This falls into the 75-89 range..."
- ❌ "Vague statements without specific numbers..."
- ❌ "Score is high due to concrete data points"

**Fördert**:
- ✅ "The 100% tariff announcement will trigger..."
- ✅ "China's export controls threaten global supply chains..."
- ✅ "November 1st deadline gives markets limited time..."

---

## Pipeline Flow

```
Post Text
    ↓
[Market Analysis Prompt]
    ↓
Analysis (Score, Reasoning, Market Direction)
    ↓
[Quality Check Prompt]
    ↓
QC Result (approved: true/false, suggested_fixes)
    ↓
Apply Fixes if needed
    ↓
Discord Alert (Final Analysis)
```

## Verwendung

```python
from prompts.market_analysis_prompt import build_market_analysis_prompt
from prompts.quality_check_prompt import build_quality_check_prompt

# Stufe 1: Market Analysis
prompt1 = build_market_analysis_prompt(post_text)
analysis = llm.generate(prompt1)

# Stufe 2: Quality Check
prompt2 = build_quality_check_prompt(
    post_text=post_text,
    score=analysis['score'],
    reasoning=analysis['reasoning'],
    urgency=analysis['urgency'],
    market_impact="formatted market impact string"
)
qc_result = llm.generate(prompt2)

# Apply fixes if needed
if not qc_result['approved'] and qc_result['suggested_fixes']:
    analysis.update(qc_result['suggested_fixes'])
```

## Konfiguration

**LLM Settings für Market Analysis**:
- Temperature: 0.1 (consistent scoring)
- num_predict: 2000 tokens (comprehensive reasoning)
- timeout: 60s (thorough analysis)
- enable_thinking: default (Qwen3 can think for better reasoning)

**LLM Settings für Quality Check**:
- Temperature: 0.7 (Qwen3 Best Practice for non-thinking mode)
- TopP: 0.8 (Qwen3 Best Practice)
- TopK: 20 (Qwen3 Best Practice)
- MinP: 0 (Qwen3 Best Practice)
- num_predict: 800 tokens (shorter than main analysis)
- timeout: 30s (faster QC)
- **enable_thinking: False** ⚠️ WICHTIG! Deaktiviert Qwen3 thinking mode für direkte JSON response

> **Reference**: [Qwen3-8B Best Practices](https://huggingface.co/Qwen/Qwen3-8B#best-practices)
> "For non-thinking mode (enable_thinking=False), we suggest using Temperature=0.7, TopP=0.8, TopK=20, and MinP=0."

## Training Data

Quality Check Ergebnisse werden in `training_data/llm_training_data.jsonl` gespeichert:

```json
{
  "timestamp": "2025-10-11T18:20:00Z",
  "post_text": "...",
  "keyword_score": 75,
  "llm_score": 90,
  "llm_reasoning": "...",
  "urgency": "immediate",
  "quality_check": {
    "approved": true,
    "quality_score": 95,
    "issues_found": []
  }
}
```

Diese Daten können später für:
- spaCy NER Training verwendet werden
- Prompt Verbesserungen analysieren
- Model Performance Tracking

## Zukünftige Prompts

Weitere Prompts können hier hinzugefügt werden:
- `sentiment_analysis_prompt.py` - Sentiment Analyse
- `entity_extraction_prompt.py` - Named Entity Recognition
- `trend_detection_prompt.py` - Trend Erkennung
- etc.

---

**Letzte Aktualisierung**: 11. Oktober 2025  
**Version**: 2.0 (Zweistufige Analyse mit Quality Check)
