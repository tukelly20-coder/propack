# ollama_client.py - Ollama AI Client Wrapper
# Provides unified interface for local Ollama server
import json
import requests
from typing import Dict, List, Optional, Tuple, Generator

class OllamaClient:
    """Ollama AI Client with streaming support"""
    
    DEFAULT_URLS = [
        'http://localhost:11434',
        'http://127.0.0.1:11434',
        'http://0.0.0.0:11434',
    ]
    
    def __init__(self, url: str = 'http://localhost:11434', enabled: bool = True):
        self.url = url
        self.enabled = enabled
    
    def _get_working_url(self) -> Optional[str]:
        """Auto-discover working Ollama URL"""
        for url in self.DEFAULT_URLS:
            try:
                resp = requests.get(f"{url}/api/tags", timeout=3)
                if resp.ok:
                    return url
            except:
                continue
        return None
    
    def generate_content(self, model: str, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate content from Ollama"""
        if not self.enabled:
            return None, "Ollama is disabled"
        
        try:
            target_url = f"{self.url}/api/generate"
            resp = requests.post(
                target_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if resp.status_code >= 400:
                return None, f"Error {resp.status_code}: {resp.text[:200]}"
            
            result = resp.json()
            return result.get('response', ''), None
            
        except requests.exceptions.ConnectionError:
            return None, "Cannot connect to Ollama server"
        except requests.exceptions.Timeout:
            return None, "Request timeout"
        except Exception as e:
            return None, str(e)
    
    def generate_stream(self, model: str, prompt: str) -> Generator:
        """Generate content with streaming"""
        if not self.enabled:
            yield {"error": "Ollama is disabled"}
            return
        
        try:
            target_url = f"{self.url}/api/generate"
            
            yield {"type": "status", "value": "sending"}
            yield {"type": "status", "value": "thinking"}
            
            resp = requests.post(
                target_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=120
            )
            
            if resp.status_code >= 400:
                yield {"error": f"Error {resp.status_code}: {resp.text[:200]}"}
                return
            
            full_response = ""
            yield {"type": "status", "value": "streaming"}
            
            for line in resp.iter_lines():
                if line:
                    try:
                        data_json = json.loads(line.decode('utf-8'))
                        
                        if 'response' in data_json:
                            chunk = data_json['response']
                            full_response += chunk
                            yield {"type": "chunk", "content": chunk, "full": full_response}
                        
                        if data_json.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            yield {"type": "status", "value": "done"}
            yield {"type": "done", "full": full_response}
            
        except requests.exceptions.ConnectionError as e:
            yield {"error": f"Cannot connect to Ollama: {str(e)}"}
        except Exception as e:
            yield {"error": str(e)}
    
    def list_models(self) -> Tuple[List[Dict], Optional[str]]:
        """Get available models"""
        if not self.enabled:
            return [], "Ollama is disabled"
        
        try:
            resp = requests.get(f"{self.url}/api/tags", timeout=10)
            
            if resp.status_code >= 400:
                return [], f"Error {resp.status_code}"
            
            result = resp.json()
            models = result.get('models', [])
            return models, None
            
        except Exception as e:
            return [], str(e)
    
    def check_connection(self) -> Tuple[bool, Optional[str]]:
        """Check if Ollama is accessible"""
        if not self.enabled:
            return False, "Ollama is disabled"
        
        try:
            resp = requests.get(f"{self.url}/api/tags", timeout=5)
            
            if resp.ok:
                return True, None
            else:
                return False, f"HTTP {resp.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect - is Ollama running?"
        except Exception as e:
            return False, str(e)


# Factory function
def create_ollama_client(url: str = 'http://localhost:11434', enabled: bool = True) -> OllamaClient:
    """Create Ollama client instance"""
    return OllamaClient(url, enabled)
