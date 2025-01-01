import subprocess
import time
import requests
import logging

class OllamaService:
    def __init__(self):
        self.model = "electromagneticcyclone/t-lite-q:3_k_l"
        
    def start(self):
        try:
            subprocess.Popen(['ollama', 'serve'])
            time.sleep(5)
            subprocess.run(['ollama', 'pull', self.model])
            return True
        except Exception as e:
            logging.error(f"Ollama startup error: {e}")
            return False

    def process_text(self, text):
        try:
            response = requests.post('http://localhost:11434/api/generate', 
                json={
                    "model": self.model,
                    "prompt": f"Исправь грамматические ошибки и пунктуацию в тексте: {text}. В ответ напиши только исправленную версию, ничего больше.",
                    "stream": False,
                    "temperature": 0.1
                })
                
            data = response.json()
            if 'response' in data:
                return data['response']
            else:
                logging.error(f"Unexpected Ollama response: {data}")
                return text
                
        except Exception as e:
            logging.error(f"Ollama processing error: {e}")
            return text

    def summarize_text(self, text):
        try:
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    "model": self.model,
                    "prompt": f"Сделай краткое описание текста в нескольких пунктах: {text}",
                    "stream": False,
                    "temperature": 0.1,
                    "max_tokens": 300
                })
                
            data = response.json()
            if 'response' in data:
                return data['response']
            else:
                logging.error(f"Unexpected Ollama response: {data}")
                return "Не удалось создать краткое описание"
                
        except Exception as e:
            logging.error(f"Ollama summarization error: {e}")
            return "Ошибка при создании краткого описания"