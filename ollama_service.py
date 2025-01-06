import subprocess
import time
import requests
import logging

class OllamaService:
    def __init__(self):
        self.default_model = "electromagneticcyclone/t-lite-q:3_k_l"
        self.loaded_models = set()

    def start(self):
        try:
            subprocess.Popen(['ollama', 'serve'])
            time.sleep(5)
            self.load_model(self.default_model)
            return True
        except Exception as e:
            logging.error(f"Ollama startup error: {e}")
            return False

    def load_model(self, model_name):
        if model_name in self.loaded_models:
            return True
        try:
            subprocess.run(['ollama', 'pull', model_name], check=True)
            self.loaded_models.add(model_name)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to load model {model_name}: {e}")
            return False

    def process_text(self, text, model_name=None):
        model = model_name or self.default_model
        if not self.load_model(model):
            return text

        try:
            response = requests.post('http://localhost:11434/api/generate', 
                json={
                    "model": model,
                    "prompt": f"Исправь грамматические ошибки и пунктуацию в тексте: {text}. В ответ напиши только исправленную версию, ничего больше.",
                    "stream": False,
                    "temperature": 0.1
                })
                
            data = response.json()
            return data.get('response', text)
        except Exception as e:
            logging.error(f"Ollama processing error: {e}")
            return text

    def summarize_text(self, text, model_name=None):
        model = model_name or self.default_model
        if not self.load_model(model):
            return "Ошибка загрузки модели"

        try:
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    "model": model,
                    "prompt": f"Сделай краткое описание текста в нескольких пунктах: {text}",
                    "stream": False,
                    "temperature": 0.1,
                    "max_tokens": 300
                })
                
            data = response.json()
            return data.get('response', "Не удалось создать краткое описание")
        except Exception as e:
            logging.error(f"Ollama summarization error: {e}")
            return "Ошибка при создании краткого описания"

    def answer_question(self, text, question, model_name=None):
        model = model_name or self.default_model
        if not self.load_model(model):
            return "Ошибка загрузки модели"

        try:
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    "model": model,
                    "prompt": f"Текст: {text}\n\nВопрос: {question}\n\nОтветь на вопрос используя только информацию из текста.",
                    "stream": False,
                    "temperature": 0.1,
                    "max_tokens": 200
                })
                
            data = response.json()
            return data.get('response', "Не удалось получить ответ")
        except Exception as e:
            logging.error(f"Ollama question answering error: {e}")
            return "Ошибка при обработке вопроса"