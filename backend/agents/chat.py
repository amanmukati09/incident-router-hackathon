import requests
import sys

class ChatAgent:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    def generate_response(self, user_message: str, chat_history: list) -> str:
        system_prompt = "You are AegisAI, an expert Site Reliability Engineering (SRE) assistant. Be helpful, professional, and conversational."
        prompt = f"{system_prompt}\n\nUser: {user_message}\nAI:"
        
        try:
            # FIX: Increased timeout from 5 to 120 seconds to allow the model to load into RAM!
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=120 
            )
            if response.status_code == 200:
                return response.json().get("response", "Error generating response.")
            else:
                return self._mock_fallback(user_message)
        except Exception as e:
            # If Ollama isn't running, gracefully fallback
            print(f"Ollama Error: {e}") # This will print to terminal so you know if it failed
            return self._mock_fallback(user_message)

    def _mock_fallback(self, msg: str) -> str:
        msg = msg.lower()
        if "hello" in msg or "hi " in msg or msg.strip() == "hi":
            return "Hello! 👋 I am AegisAI, your intelligent SRE Copilot. How can I help you investigate your infrastructure today?"
        elif "version" in msg or "python" in msg:
            return f"I can certainly help with that! The backend is currently running on **Python {sys.version.split(' ')[0]}**."
        elif "log" in msg or "error" in msg or "anomaly" in msg:
            return "I am analyzing the logs. This signature typically indicates resource exhaustion or a sudden crash. Would you like me to generate a bash script to restart the service?"
        else:
            return "I am operating in fallback mode (Ollama is currently unreachable). However, I'm still recording this session! What else would you like to discuss?"