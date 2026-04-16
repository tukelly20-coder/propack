# gemini_client.py - Gemini AI Client Wrapper
# Provides unified interface for Gemini API calls
import json
import requests
from typing import Dict, List, Optional, Tuple

class GeminiClient:
    """Gemini AI Client with streaming support"""
    
    def __init__(self, api_key: str, model: str = 'gemini-3-flash-preview'):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    def generate_content(self, contents: List[Dict], system_instruction: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Generate content from Gemini API"""
        if not self.api_key:
            return None, "API key not configured"
        
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        # Build payload
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 2048,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "role": "user",
                "parts": [{"text": system_instruction}]
            }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if resp.status_code >= 400:
                return None, f"API Error {resp.status_code}: {resp.text[:200]}"
            
            result = resp.json()
            response_text = ""
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    response_text = "\n".join([p.get('text', '') for p in parts])
            
            return response_text or "Không có phản hồi từ AI", None
            
        except requests.exceptions.Timeout:
            return None, "Request timeout"
        except Exception as e:
            return None, str(e)
    
    def generate_stream(self, contents: List[Dict], system_instruction: Optional[str] = None):
        """Generate content with simulated streaming"""
        if not self.api_key:
            yield {"error": "API key not configured"}
            return
        
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 2048,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "role": "user",
                "parts": [{"text": system_instruction}]
            }
        
        try:
            yield {"type": "status", "value": "thinking"}
            
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if resp.status_code >= 400:
                yield {"type": "status", "value": "error"}
                yield {"error": f"API Error {resp.status_code}"}
                return
            
            result = resp.json()
            response_text = ""
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    response_text = "\n".join([p.get('text', '') for p in parts])
            
            if not response_text:
                response_text = "Không có phản hồi từ AI"
            
            yield {"type": "status", "value": "streaming"}
            
            # Simulate streaming with chunks
            chunk_size = 20
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield {"type": "chunk", "content": chunk, "full": response_text}
            
            yield {"type": "status", "value": "done"}
            yield {"type": "done", "full": response_text}
            
        except Exception as e:
            yield {"type": "status", "value": "error"}
            yield {"error": str(e)}
    
    def check_connection(self) -> Tuple[bool, Optional[str]]:
        """Check if API key is valid"""
        if not self.api_key:
            return False, "API key not set"
        
        try:
            # Quick test with minimal request
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            resp = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                json={"contents": [{"role": "user", "parts": [{"text": "test"}]}]},
                timeout=10
            )
            
            if resp.status_code < 400:
                return True, None
            else:
                return False, f"HTTP {resp.status_code}"
                
        except Exception as e:
            return False, str(e)


# Factory function to create client
def create_gemini_client(api_key: str, model: str = 'gemini-3-flash-preview') -> GeminiClient:
    """Create Gemini client instance"""
    return GeminiClient(api_key, model)
