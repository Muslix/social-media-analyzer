"""
LLM-based Market Impact Analyzer using Ollama
Provides intelligent semantic analysis for posts that pass keyword filter
"""
import json
import logging
import requests
from typing import Dict, Optional, TYPE_CHECKING
from datetime import datetime, UTC
import time
import sys
import os

# Add prompts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../prompts'))
from market_analysis_prompt import build_market_analysis_prompt
from quality_check_prompt import build_quality_check_prompt

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from src.config import Config

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """
    Intelligent LLM-based market analysis using Ollama
    Uses CPU-optimized LLM model (default: Llama 3.2 3B)
    """
    
    def __init__(self,
                 ollama_url: Optional[str] = None,
                 model: Optional[str] = None,
                 timeout: int = 1200,
                 config: Optional["Config"] = None):  # Increased from 30 to 60 seconds
        """
        Initialize LLM Analyzer
        
        Args:
            ollama_url: Ollama server URL (default: from config)
            model: Model name (default: from config - llama3.2:3b for CPU efficiency)
            timeout: Request timeout in seconds (120s for thorough analysis)
        """
        # Import config for defaults (lazy to avoid circular imports on type checking)
        if config is None:
            from src.config import Config  # Local import keeps module load cheap
            config = Config()

        self.config = config

        # OpenRouter configuration
        self.use_openrouter = getattr(self.config, "OPENROUTER_ENABLED", False)
        self.openrouter_model = getattr(self.config, "OPENROUTER_MODEL", None)
        self.openrouter_url = getattr(self.config, "OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
        self.openrouter_api_key = getattr(self.config, "OPENROUTER_API_KEY", None)
        self.openrouter_referer = getattr(self.config, "OPENROUTER_REFERER", None)
        self.openrouter_title = getattr(self.config, "OPENROUTER_TITLE", None)
        self.openrouter_timeout = getattr(self.config, "OPENROUTER_TIMEOUT", timeout)
        self._openrouter_headers = self._build_openrouter_headers() if self.use_openrouter and self.openrouter_api_key else {}
        self.openrouter_min_interval = float(getattr(self.config, "OPENROUTER_MIN_INTERVAL", 5.0) or 0)
        self._openrouter_last_call: float = 0.0

        # Ollama configuration
        self.ollama_url = ollama_url or self.config.OLLAMA_URL
        self.model = model or self.config.OLLAMA_MODEL
        self.timeout = timeout
        self.num_threads = self.config.OLLAMA_NUM_THREADS

        self.error_webhook_url = getattr(self.config, "LLM_ERROR_WEBHOOK_URL", None)
        self._last_raw_response: Optional[str] = None

        # Verify primary connection
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify configured LLM provider is available"""
        if self.use_openrouter:
            if not self.openrouter_api_key:
                logger.error("❌ OpenRouter is enabled but OPENROUTER_API_KEY is missing. Falling back to Ollama.")
                self.use_openrouter = False
            else:
                logger.info(f"✅ OpenRouter enabled - using model '{self.openrouter_model}'")
                return

        self._verify_ollama()

    def _verify_ollama(self):
        """Verify Ollama server is accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info(f"✅ Connected to Ollama at {self.ollama_url}")

            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]

            if not any(self.model in name for name in model_names):
                logger.warning(f"⚠️  Model '{self.model}' not found. Available: {model_names}")
            else:
                logger.info(f"✅ Model '{self.model}' is available")

        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            logger.info("Make sure Ollama is running: ollama serve")

    def _build_openrouter_headers(self) -> Dict[str, str]:
        """Build HTTP headers required for OpenRouter requests"""
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        if self.openrouter_referer:
            headers["HTTP-Referer"] = self.openrouter_referer

        if self.openrouter_title:
            headers["X-Title"] = self.openrouter_title

        return headers

    def _run_llm(
        self,
        prompt: str,
        *,
        options: Dict,
        timeout: int,
        response_format: Optional[Dict],
        openrouter_settings: Optional[Dict],
        context: str,
    ) -> tuple[str, str]:
        """
        Execute the LLM call, preferring OpenRouter when enabled and falling back to Ollama.

        Returns:
            Tuple of (response_text, provider_used)
        """
        if self.use_openrouter:
            try:
                response_text = self._invoke_openrouter(
                    prompt,
                    response_format=response_format,
                    temperature=(openrouter_settings or {}).get("temperature"),
                    top_p=(openrouter_settings or {}).get("top_p"),
                    max_output_tokens=(openrouter_settings or {}).get("max_output_tokens"),
                )
                return response_text, "openrouter"
            except Exception as exc:
                logger.error(f"❌ OpenRouter {context} request failed: {exc}")
                if not self.ollama_url:
                    raise
                logger.info(f"⚠️  Falling back to Ollama for {context}")

        response_text, _ = self._invoke_ollama(prompt, options=options, timeout=timeout)
        return response_text, "ollama"

    def _invoke_openrouter(
        self,
        prompt: str,
        *,
        response_format: Optional[Dict],
        temperature: Optional[float],
        top_p: Optional[float],
        max_output_tokens: Optional[int],
    ) -> str:
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key is not configured")

        payload: Dict[str, object] = {
            "model": self.openrouter_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if max_output_tokens is not None:
            payload["max_output_tokens"] = max_output_tokens
        if response_format:
            payload["response_format"] = response_format

        if self.openrouter_min_interval > 0:
            now = time.time()
            elapsed = now - self._openrouter_last_call
            if elapsed < self.openrouter_min_interval:
                wait_for = self.openrouter_min_interval - elapsed
                if wait_for > 0:
                    logger.debug(
                        "Throttling OpenRouter request by %.2fs to respect rate limit",
                        wait_for
                    )
                    time.sleep(wait_for)
            self._openrouter_last_call = time.time()

        response = requests.post(
            self.openrouter_url,
            headers=self._openrouter_headers,
            json=payload,
            timeout=self.openrouter_timeout,
        )
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("OpenRouter returned no choices")

        message = choices[0].get("message", {})
        content = message.get("content", "")

        if isinstance(content, list):
            content = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )

        if not isinstance(content, str):
            raise ValueError("OpenRouter response content is not textual")

        content = content.strip()
        if not content:
            raise ValueError("OpenRouter returned empty content")

        return content

    def _invoke_ollama(
        self,
        prompt: str,
        *,
        options: Dict,
        timeout: int,
    ) -> tuple[str, Dict]:
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": options,
            },
            timeout=timeout,
        )
        response.raise_for_status()

        result = response.json()
        llm_response = result.get("response", "").strip()

        if not llm_response and "thinking" in result:
            thinking = result.get("thinking", "").strip()
            if thinking and (thinking.startswith("{") or "{" in thinking):
                logger.debug("Using 'thinking' field from Qwen3 (contains JSON)")
                llm_response = thinking
            else:
                logger.warning("⚠️  Qwen3 returned thinking but no JSON found")
                logger.debug(f"Thinking: {thinking[:200]}..." if thinking else "Thinking field was empty")
                raise ValueError("Empty response, thinking contains no JSON")

        return llm_response, result
    
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
                
                # Build options dict
                options = {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 4000,  # Increased to ensure complete responses
                }

                # Add num_thread if configured (CPU optimization)
                if self.num_threads > 0:
                    options["num_thread"] = self.num_threads

                try:
                    llm_response, provider_used = self._run_llm(
                        prompt=prompt,
                        options=options,
                        timeout=self.timeout,
                        response_format={"type": "json_object"},
                        openrouter_settings={
                            "temperature": options.get("temperature"),
                            "top_p": options.get("top_p"),
                            "max_output_tokens": options.get("num_predict"),
                        },
                        context="analysis",
                    )
                except ValueError as val_err:
                    last_error = str(val_err)
                    logger.warning(f"⚠️  {last_error} (attempt {attempt + 1}/{max_retries})")
                    continue

                model_name = self.openrouter_model if provider_used == "openrouter" else self.model

                if not llm_response:
                    last_error = "Empty response from LLM"
                    logger.warning(f"⚠️  {last_error} (attempt {attempt + 1}/{max_retries})")
                    continue

                # Check if response is incomplete (missing closing braces)
                if llm_response.count('{') > llm_response.count('}'):
                    missing_braces = llm_response.count('{') - llm_response.count('}')
                    logger.warning(f"⚠️  Incomplete JSON detected, adding {missing_braces} closing brace(s)")
                    llm_response += '\n' + '}' * missing_braces

                self._last_raw_response = llm_response

                # Debug: Log response details
                logger.debug(f"LLM response length: {len(llm_response)} chars (attempt {attempt + 1}/{max_retries})")
                if len(llm_response) < 500:
                    logger.warning(f"Short LLM response ({len(llm_response)} chars): {llm_response}")
                else:
                    logger.debug(f"LLM response preview: {llm_response[:200]}...{llm_response[-200:]}")

                processing_time = time.time() - start_time

                # Try to parse JSON from response
                analysis = self._parse_llm_response(llm_response)

                if analysis:
                    analysis['processing_time_seconds'] = round(processing_time, 2)
                    analysis['model'] = model_name
                    analysis['provider'] = provider_used
                    analysis['keyword_score'] = keyword_score

                    provider_label = "OpenRouter" if provider_used == "openrouter" else "Ollama"
                    if attempt > 0:
                        logger.info(
                            f"✅ LLM Analysis succeeded on retry {attempt + 1}/{max_retries} via {provider_label} "
                            f"in {processing_time:.2f}s - Score: {analysis.get('score', 'N/A')}"
                        )
                    else:
                        logger.info(
                            f"✅ LLM Analysis complete via {provider_label} in {processing_time:.2f}s - "
                            f"Score: {analysis.get('score', 'N/A')}"
                        )
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
        self._notify_failure(
            post_text=post_text,
            keyword_score=keyword_score,
            error_message=last_error,
        )
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
            
            # Build options dict - Qwen3 Best Practices for non-thinking mode
            # https://huggingface.co/Qwen/Qwen3-8B
            options = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 20,
                "min_p": 0,
                "num_predict": 800,
                "enable_thinking": False,  # Disable thinking mode for direct JSON
            }
            
            # Add num_thread if configured (CPU optimization)
            if self.num_threads > 0:
                options["num_thread"] = self.num_threads
            
            try:
                qc_response, qc_provider = self._run_llm(
                    prompt=prompt,
                    options=options,
                    timeout=30,  # Shorter timeout for QC
                    response_format={"type": "json_object"},
                    openrouter_settings={
                        "temperature": options.get("temperature"),
                        "top_p": options.get("top_p"),
                        "max_output_tokens": options.get("num_predict"),
                    },
                    context="quality check",
                )
            except ValueError as val_err:
                logger.warning(f"⚠️  Quality check LLM error: {val_err}")
                return None

            if not qc_response:
                logger.warning("⚠️  Quality check returned empty response")
                return None
            
            # Debug log
            logger.debug(f"QC Response length: {len(qc_response)} chars")
            if len(qc_response) < 100:
                logger.warning(f"Short QC response: {qc_response[:200] if qc_response else 'EMPTY'}")
            
            # Parse JSON
            qc_result = self._parse_llm_response(qc_response)
            
            if qc_result:
                provider_label = "OpenRouter" if qc_provider == "openrouter" else "Ollama"
                logger.info(f"✅ Quality Check: {'APPROVED' if qc_result.get('approved') else 'NEEDS FIXES'} (Quality: {qc_result.get('quality_score', 0)}/100)")
                logger.debug(f"Quality check provider: {provider_label}")
                
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
            parsed = json.loads(response_text, strict=False)
            # Validate it has expected structure
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        
        # Try 2: Extract from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1), strict=False)
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
                return json.loads(json_match.group(0), strict=False)
            except json.JSONDecodeError:
                pass

        # Try 5: Final fallback - sanitize JSON-like responses
        sanitized = self._sanitize_json_candidate(response_text)
        if sanitized:
            try:
                parsed = json.loads(sanitized, strict=False)
                if isinstance(parsed, dict) and 'score' in parsed and 'reasoning' in parsed:
                    return parsed
            except json.JSONDecodeError as exc:
                logger.debug(f"Sanitized JSON parse failed: {exc}")
        
        # Try 6: Last resort - try to fix truncated JSON by adding missing closing braces
        if '{' in response_text and response_text.count('{') > response_text.count('}'):
            missing = response_text.count('{') - response_text.count('}')
            truncated_fix = response_text + ('}' * missing)
            try:
                parsed = json.loads(truncated_fix, strict=False)
                if isinstance(parsed, dict) and 'score' in parsed:
                    logger.warning("⚠️  Recovered truncated JSON response by adding closing braces")
                    return parsed
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not parse JSON from response. First 300 chars: {response_text[:300]}")
        return None

    @staticmethod
    def _sanitize_json_candidate(raw_text: str) -> Optional[str]:
        """Attempt to coerce almost-JSON into valid JSON."""
        if not raw_text:
            return None

        start = raw_text.find('{')
        end = raw_text.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None

        candidate = raw_text[start:end + 1]
        
        # Fix terminal line wrapping issues (like "A s\ntronger" -> "A stronger")
        # This happens when terminal wraps long lines - we need to join them back
        import re
        # Replace line breaks that are clearly mid-word wrapping
        candidate = re.sub(r'([a-z])\s*\n\s*([a-z])', r'\1\2', candidate)
        
        candidate = candidate.replace('\r\n', '\n').replace('\r', '\n')

        result_chars = []
        in_string = False
        escape_next = False

        for idx, char in enumerate(candidate):
            if in_string:
                if escape_next:
                    result_chars.append(char)
                    escape_next = False
                    continue

                if char == '\\':
                    result_chars.append(char)
                    escape_next = True
                    continue

                if char == '"':
                    # Look ahead to determine if this should be escaped
                    look_ahead_idx = idx + 1
                    while look_ahead_idx < len(candidate) and candidate[look_ahead_idx].isspace():
                        look_ahead_idx += 1
                    if look_ahead_idx < len(candidate) and candidate[look_ahead_idx] not in ',:}]':
                        # Treat as interior quote -> escape it
                        result_chars.append('\\')
                        result_chars.append('"')
                        continue
                    else:
                        # Closing quote
                        result_chars.append(char)
                        in_string = False
                        continue

                if char == '\n':
                    result_chars.append('\\')
                    result_chars.append('n')
                    continue

                if char == '\t':
                    result_chars.append('\\')
                    result_chars.append('t')
                    continue

                # Remove carriage returns outright
                if char == '\r':
                    continue

                result_chars.append(char)
            else:
                result_chars.append(char)
                if char == '"':
                    in_string = True
                    escape_next = False

        sanitized = ''.join(result_chars)

        # Remove trailing commas before closing braces/brackets
        import re
        sanitized = re.sub(r',(\s*[}\]])', r'\1', sanitized)

        # If we exited while still inside a string, close it
        if in_string:
            sanitized += '"'

        # Balance braces if truncated
        open_braces = sanitized.count('{')
        close_braces = sanitized.count('}')
        if open_braces > close_braces:
            sanitized += '}' * (open_braces - close_braces)

        return sanitized

    def _notify_failure(self, *, post_text: str, keyword_score: int, error_message: Optional[str]) -> None:
        """Send failure details to configured Discord webhook."""
        if not self.error_webhook_url:
            return

        try:
            post_preview = (post_text or "").strip()
            post_preview = post_preview[:600] + ("…" if len(post_preview) > 600 else "")

            raw_preview = (self._last_raw_response or "").strip()
            raw_preview = raw_preview[:600] + ("…" if len(raw_preview) > 600 else "")

            content_lines = [
                "⚠️ **LLM Analysis Failed**",
                f"• Model: `{self.model}`",
                f"• Keyword Score: `{keyword_score}`",
                f"• Reason: `{error_message or 'unknown'}`",
            ]

            if post_preview:
                content_lines.append(f"• Post Snippet: {post_preview}")
            if raw_preview:
                content_lines.append(f"• Raw Response: {raw_preview}")

            payload = {
                "content": "\n".join(content_lines)
            }

            response = requests.post(
                self.error_webhook_url,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            logger.info("📣 Reported LLM failure to Discord webhook")
        except Exception as exc:
            logger.error(f"❌ Failed to send LLM failure alert: {exc}")
    
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
