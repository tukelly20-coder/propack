# openrouter_client.py - OpenRouter AI Client Wrapper
# Provides unified interface with retry logic and fallback models
import json
import time
import random
import requests
from typing import Dict, List, Optional, Tuple, Generator

class OpenRouterClient:
    """OpenRouter AI Client with retry logic and fallback models"""
    
    DEFAULT_RETRY_CONFIG = {
        'max_retries': 3,
        'initial_delay_ms': 1000,
        'max_delay_ms': 10000,
        'timeout_seconds': 60
    }
    
    DEFAULT_FALLBACK_MODELS = [
        'meta-llama/llama-3.1-8b-instruct',
        'qwen/qwen-2.5-7b-instruct'
    ]
    
    def __init__(self, api_key: str, retry_config: Dict = None, fallback_models: List[str] = None):
        self.api_key = api_key
        self.retry_config = retry_config or self.DEFAULT_RETRY_CONFIG
        self.fallback_models = fallback_models or self.DEFAULT_FALLBACK_MODELS
        self.base_url = "https://openrouter.ai/api/v1"
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Calculate delay with exponential backoff"""
        initial_delay = self.retry_config.get('initial_delay_ms', 1000)
        max_delay = self.retry_config.get('max_delay_ms', 10000)
        delay = min(initial_delay * (2 ** attempt), max_delay)
        jitter = random.randint(0, 1000)
        return (delay + jitter) / 1000
    
    def _is_rate_limit_error(self, response) -> bool:
        """Check if response indicates rate limiting (429)"""
        try:
            data = response.json() if hasattr(response, 'json') else json.loads(response)
            if isinstance(data, dict):
                error = data.get('error', {})
                if isinstance(error, dict):
                    code = error.get('code', 0)
                    if code == 429:
                        return True
                    msg = str(error.get('message', '')).lower()
                    if 'rate' in msg and 'limit' in msg:
                        return True
        except:
            pass
        return False
    
    def generate_content(self, model: str, messages: List[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """Generate content with retry logic"""
        if not self.api_key:
            return None, "API key not configured"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': messages,
            'stream': False
        }
        
        max_retries = self.retry_config.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.retry_config.get('timeout_seconds', 60)
                )
                
                # Check for rate limit
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        delay = self._exponential_backoff(attempt)
                        time.sleep(delay)
                        continue
                    break
                
                if resp.status_code >= 400:
                    # Check for rate limit in response body
                    if self._is_rate_limit_error(resp):
                        if attempt < max_retries - 1:
                            delay = self._exponential_backoff(attempt)
                            time.sleep(delay)
                            continue
                    break
                
                result = resp.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    return content, None
                
                return None, "No content in response"
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    time.sleep(delay)
                    continue
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    time.sleep(delay)
                    continue
                return None, str(e)
        
        # Try fallback models
        for fallback_model in self.fallback_models:
            if fallback_model == model:
                continue
            
            try:
                fallback_payload = payload.copy()
                fallback_payload['model'] = fallback_model
                
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=fallback_payload,
                    timeout=self.retry_config.get('timeout_seconds', 60)
                )
                
                if resp.status_code == 429:
                    continue
                
                if resp.status_code >= 400:
                    continue
                
                result = resp.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    return content, None
                    
            except Exception:
                continue
        
        return None, "All retry attempts and fallback models failed"
    
    def generate_stream(self, model: str, messages: List[Dict]) -> Generator:
        """Generate content with streaming and retry"""
        if not self.api_key:
            yield {"error": "API key not configured"}
            return
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }
        
        payload = {
            'model': model,
            'messages': messages,
            'stream': True
        }
        
        max_retries = self.retry_config.get('max_retries', 3)
        models_tried = [model]
        
        # Try original model with retries
        for attempt in range(max_retries):
            try:
                yield {"type": "status", "value": "sending"}
                yield {"type": "status", "value": "thinking"}
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=120
                )
                
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        delay = self._exponential_backoff(attempt)
                        yield {"type": "status", "value": "retrying", "delay": delay}
                        time.sleep(delay)
                        continue
                    break
                
                if response.status_code >= 400:
                    if attempt < max_retries - 1 and self._is_rate_limit_error(response):
                        delay = self._exponential_backoff(attempt)
                        yield {"type": "status", "value": "retrying", "delay": delay}
                        time.sleep(delay)
                        continue
                    break
                
                # Process streaming
                full_response = ""
                yield {"type": "status", "value": "streaming"}
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                chunk_data = json.loads(line[6:])
                                
                                if chunk_data == '[DONE]':
                                    break
                                
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        content = delta['content']
                                        full_response += content
                                        yield {"type": "chunk", "content": content, "full": full_response}
                            except json.JSONDecodeError:
                                continue
                
                yield {"type": "status", "value": "done"}
                yield {"type": "done", "full": full_response}
                return
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    time.sleep(delay)
                    continue
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    time.sleep(delay)
                    continue
                break
        
        # Try fallback models
        available_fallbacks = [m for m in self.fallback_models if m not in models_tried]
        
        for fallback_model in available_fallbacks:
            try:
                models_tried.append(fallback_model)
                
                fallback_payload = payload.copy()
                fallback_payload['model'] = fallback_model
                
                yield {"type": "start", "model_switched": fallback_model}
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=fallback_payload,
                    stream=True,
                    timeout=120
                )
                
                if response.status_code == 429:
                    continue
                
                if response.status_code >= 400:
                    continue
                
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                chunk_data = json.loads(line[6:])
                                
                                if chunk_data == '[DONE]':
                                    break
                                
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        content = delta['content']
                                        full_response += content
                                        yield {"type": "chunk", "content": content, "full": full_response}
                            except json.JSONDecodeError:
                                continue
                
                yield {"type": "done", "full": full_response, "model_used": fallback_model}
                return
                
            except Exception:
                continue
        
        yield {"type": "status", "value": "error"}
        yield {"error": "All models failed. Please try again later."}
    
    def check_connection(self) -> Tuple[bool, Optional[str]]:
        """Check if API key is valid"""
        if not self.api_key:
            return False, "API key not set"
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            resp = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code < 400:
                return True, None
            else:
                return False, f"HTTP {resp.status_code}"
                
        except Exception as e:
            return False, str(e)


# Factory function to create client
def create_openrouter_client(api_key: str, retry_config: Dict = None, fallback_models: List[str] = None) -> OpenRouterClient:
    """Create OpenRouter client instance"""
    return OpenRouterClient(api_key, retry_config, fallback_models)
