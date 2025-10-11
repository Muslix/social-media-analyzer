"""
LLM-based Market Impact Analyzer using Ollama
Provides intelligent semantic analysis for posts that pass keyword filter
"""
import json
import logging
import requests
from typing import Dict, Optional
from datetime import datetime, UTC
import time
import sys
import os

# Add prompts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../prompts'))
from market_analysis_prompt import build_market_analysis_prompt
from quality_check_prompt import build_quality_check_prompt

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """
    Intelligent LLM-based market analysis using Ollama
    Uses local Qwen2.5:3b model for CPU-efficient semantic analysis
    """
    
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 model: str = "qwen3:8b",
                 timeout: int = 1200):  # Increased from 30 to 60 seconds
        """
        Initialize LLM Analyzer
        
        Args:
            ollama_url: Ollama server URL
            model: Model name (default: qwen3:8b - better reasoning)
            timeout: Request timeout in seconds (120s for thorough analysis)
        """
        self.ollama_url = ollama_url
        self.model = model
        self.timeout = timeout
        
        # Verify Ollama is accessible
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Ollama server is accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info(f"✅ Connected to Ollama at {self.ollama_url}")
            
            # Check if model is available
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            if not any(self.model in name for name in model_names):
                logger.warning(f"⚠️  Model '{self.model}' not found. Available: {model_names}")
            else:
                logger.info(f"✅ Model '{self.model}' is available")
                
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            logger.info("Make sure Ollama is running: ollama serve")
    
    def analyze(self, post_text: str, keyword_score: int, max_retries: int = 3) -> Optional[Dict]:
        """
        Analyze post text using LLM for market impact with automatic retries
        
        Args:
            post_text: The post text to analyze
            keyword_score: Pre-computed keyword-based score for context
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Dict with LLM analysis or None if all retries fail
        """
        if not post_text or not post_text.strip():
            return None
        
        # Build the analysis prompt using template
        prompt = build_market_analysis_prompt(post_text)
        
        # Retry loop
        last_error = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry attempt {attempt + 1}/{max_retries}")
                    time.sleep(2)  # Brief delay before retry
                
                start_time = time.time()
                
                # Call Ollama API with generous limits for thorough analysis
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Slightly higher for better reasoning
                            "top_p": 0.9,
                            "num_predict": 2000,  # Increased for comprehensive reasoning
                        }
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Parse response
                result = response.json()
                llm_response = result.get('response', '').strip()
                
                # Qwen3 may put actual response in 'thinking' field with empty 'response'
                if not llm_response and 'thinking' in result:
                    thinking = result.get('thinking', '').strip()
                    if thinking and (thinking.startswith('{') or '{' in thinking):
                        logger.debug("Using 'thinking' field from Qwen3 (contains JSON)")
                        llm_response = thinking
                    else:
                        logger.warning(f"⚠️  Qwen3 returned thinking but no JSON found (attempt {attempt + 1}/{max_retries})")
                        logger.debug(f"Thinking: {thinking[:200]}...")
                        last_error = "Empty response, thinking contains no JSON"
                        continue  # Retry
                
                # Debug: Log full response if parsing might fail
                if len(llm_response) < 50 or not '{' in llm_response:
                    logger.warning(f"Suspicious LLM response length or format: {len(llm_response)} chars (attempt {attempt + 1}/{max_retries})")
                    logger.debug(f"Full LLM response: {llm_response[:200]}")
                    logger.debug(f"Full API result keys: {list(result.keys())}")
                
                processing_time = time.time() - start_time
                
                # Try to parse JSON from response
                analysis = self._parse_llm_response(llm_response)
                
                if analysis:
                    analysis['processing_time_seconds'] = round(processing_time, 2)
                    analysis['model'] = self.model
                    analysis['keyword_score'] = keyword_score
                    
                    if attempt > 0:
                        logger.info(f"✅ LLM Analysis succeeded on retry {attempt + 1}/{max_retries} in {processing_time:.2f}s - Score: {analysis.get('score', 'N/A')}")
                    else:
                        logger.info(f"✅ LLM Analysis complete in {processing_time:.2f}s - Score: {analysis.get('score', 'N/A')}")
                    return analysis
                else:
                    logger.warning(f"⚠️  Could not parse JSON from response (attempt {attempt + 1}/{max_retries})")
                    logger.debug(f"Raw LLM response: {llm_response[:500]}")
                    last_error = "JSON parsing failed"
                    # Continue to retry
                    
            except requests.exceptions.Timeout as e:
                logger.error(f"❌ LLM request timeout after {self.timeout}s (attempt {attempt + 1}/{max_retries})")
                last_error = f"Timeout: {e}"
                # Continue to retry
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ LLM request failed (attempt {attempt + 1}/{max_retries}): {e}")
                last_error = f"Request failed: {e}"
                # Continue to retry
            except Exception as e:
                logger.error(f"❌ Unexpected error in LLM analysis (attempt {attempt + 1}/{max_retries}): {e}")
                last_error = f"Unexpected error: {e}"
                # Continue to retry
        
        # All retries exhausted
        logger.error(f"❌ LLM analysis failed after {max_retries} attempts. Last error: {last_error}")
        return None
    
    def quality_check_analysis(self, post_text: str, analysis: Dict) -> Optional[Dict]:
        """
        Quality check the analysis before sending to Discord
        
        Args:
            post_text: Original post text
            analysis: The LLM analysis to check
            
        Returns:
            Dict with approval status and suggested fixes, or None if check failed
        """
        try:
            # Format market impact for readability
            market_impact = f"Stocks: {analysis.get('market_direction', {}).get('stocks', 'N/A')}, " \
                           f"Crypto: {analysis.get('market_direction', {}).get('crypto', 'N/A')}, " \
                           f"USD: {analysis.get('market_direction', {}).get('forex', 'N/A')}, " \
                           f"Commodities: {analysis.get('market_direction', {}).get('commodities', 'N/A')}"
            
            # Build quality check prompt
            prompt = build_quality_check_prompt(
                post_text=post_text,
                score=analysis.get('score', 0),
                reasoning=analysis.get('reasoning', ''),
                urgency=analysis.get('urgency', 'unknown'),
                market_impact=market_impact
            )
            
            logger.info("🔍 Running quality check on analysis...")
            
            # Call Ollama for quality check
            # IMPORTANT: Using Qwen3 Best Practices for non-thinking mode
            # https://huggingface.co/Qwen/Qwen3-8B - Best Practices section
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        # Qwen3 Best Practices for non-thinking mode:
                        "temperature": 0.7,     # Recommended for non-thinking
                        "top_p": 0.8,           # Recommended for non-thinking
                        "top_k": 20,            # Recommended for non-thinking
                        "min_p": 0,             # Recommended for non-thinking
                        "num_predict": 800,     # Shorter than main analysis
                        "enable_thinking": False,  # Disable thinking mode for direct JSON response
                    }
                },
                timeout=30  # Shorter timeout for QC
            )
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            qc_response = result.get('response', '').strip()
            
            # Debug log
            logger.debug(f"QC Response length: {len(qc_response)} chars")
            if len(qc_response) < 100:
                logger.warning(f"Short QC response: {qc_response[:200] if qc_response else 'EMPTY'}")
                logger.debug(f"Full result keys: {list(result.keys())}")
            
            # Parse JSON
            qc_result = self._parse_llm_response(qc_response)
            
            if qc_result:
                logger.info(f"✅ Quality Check: {'APPROVED' if qc_result.get('approved') else 'NEEDS FIXES'} (Quality: {qc_result.get('quality_score', 0)}/100)")
                
                if qc_result.get('issues_found'):
                    logger.warning(f"⚠️  Issues found: {', '.join(qc_result.get('issues_found', []))}")
                
                return qc_result
            else:
                logger.warning("⚠️  Could not parse quality check response")
                return None
                
        except Exception as e:
            logger.error(f"❌ Quality check failed: {e}")
            return None
    
    def _build_market_analysis_prompt(self, post_text: str, keyword_score: int) -> str:
        """
        Build a structured prompt for market impact analysis
        DEPRECATED: This method is kept for backwards compatibility
        Uses the new prompt from prompts/market_analysis_prompt.py
        """
        # Use the new centralized prompt
        return build_market_analysis_prompt(post_text)
    
    def _parse_llm_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse LLM response, extracting JSON even if there's extra text or formatting
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Parsed dict or None
        """
        import re
        
        # Remove any leading/trailing whitespace
        response_text = response_text.strip()
        
        # Try 1: Direct JSON parse (for clean responses)
        try:
            parsed = json.loads(response_text)
            # Validate it has expected structure
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        
        # Try 2: Extract from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try 3: Find balanced braces (handles nested JSON properly)
        # This is more robust for multi-line formatted JSON
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(response_text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # Found a complete JSON object
                    try:
                        json_str = response_text[start_idx:i+1]
                        parsed = json.loads(json_str)
                        # Validate it has required fields
                        if 'score' in parsed and 'reasoning' in parsed:
                            return parsed
                    except json.JSONDecodeError:
                        # Continue looking for other potential JSON objects
                        start_idx = -1
                        continue
        
        # Try 4: More aggressive regex with proper field matching
        json_match = re.search(
            r'\{\s*"score"\s*:\s*\d+\s*,.*?"reasoning"\s*:.*?"urgency"\s*:.*?\}',
            response_text,
            re.DOTALL
        )
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"Could not parse JSON from response. First 300 chars: {response_text[:300]}")
        return None
    
    def save_training_data(self, post_text: str, keyword_score: int, 
                          llm_analysis: Dict, output_dir: str = "training_data",
                          quality_check: Optional[Dict] = None):
        """
        Save analysis to training data for future spaCy NER training
        
        Args:
            post_text: Original post text
            keyword_score: Keyword-based score
            llm_analysis: LLM analysis results
            output_dir: Directory to save training data
            quality_check: Optional quality check results
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        training_entry = {
            'timestamp': datetime.now(UTC).isoformat(),
            'post_text': post_text,
            'keyword_score': keyword_score,
            'llm_score': llm_analysis.get('score', 0),
            'llm_reasoning': llm_analysis.get('reasoning', ''),
            'affected_markets': llm_analysis.get('affected_markets', []),
            'key_events': llm_analysis.get('key_events', []),
            'urgency': llm_analysis.get('urgency', 'unknown'),
            'model': llm_analysis.get('model', self.model),
            'processing_time': llm_analysis.get('processing_time_seconds', 0),
            'quality_check': quality_check  # Add QC results
        }
        
        # Append to JSONL file (one JSON per line)
        output_file = os.path.join(output_dir, 'llm_training_data.jsonl')
        
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(training_entry, ensure_ascii=False) + '\n')
            
            logger.info(f"💾 Training data saved to {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save training data: {e}")


if __name__ == "__main__":
    # Test the LLM analyzer
    logging.basicConfig(level=logging.INFO)
    
    analyzer = LLMAnalyzer()
    
    # Test with a sample post
    test_post = """
    Breaking: Fed announces emergency 0.75% interest rate hike to combat 
    rising inflation. Markets expected to react strongly.
    """
    
    print("\n" + "="*70)
    print("Testing LLM Analyzer with Qwen2.5:3b")
    print("="*70)
    print(f"\nTest Post: {test_post.strip()}")
    print("\nAnalyzing...")
    
    result = analyzer.analyze(test_post, keyword_score=45)
    
    if result:
        print("\n✅ Analysis Result:")
        print(json.dumps(result, indent=2))
    else:
        print("\n❌ Analysis failed")
