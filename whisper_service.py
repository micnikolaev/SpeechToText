import whisper
import numpy as np
import os
from typing import Optional
import logging

class WhisperService:
    # Словарь с именами файлов для каждой модели
    MODEL_FILES = {
        # Tiny модели
        'tiny': ['tiny.pt'],
        'tiny.en': ['tiny.en.pt'],
        
        # Base модели
        'base': ['base.pt'],
        'base.en': ['base.en.pt'],
        
        # Small модели
        'small': ['small.pt'],
        'small.en': ['small.en.pt'],
        
        # Medium модели
        'medium': ['medium.pt'],
        'medium.en': ['medium.en.pt'],
        
        # Large модели
        'large': ['large.pt'],
        'large-v1': ['large-v1.pt'],
        'large-v2': ['large-v2.pt'],
        'large-v3': ['large-v3.pt']
    }
    
    def __init__(self, default_model="large-v3"):
        self.model = None
        self.current_model_name = None
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.join(self.project_root, 'models', 'whisper')
        os.makedirs(self.models_dir, exist_ok=True)
        print(f"Директория для моделей Whisper: {self.models_dir}", flush=True)
    
    def get_model_path(self, model_name):
        """Получаем путь к файлу модели"""
        if model_name not in self.MODEL_FILES:
            raise ValueError(f"Неизвестная модель: {model_name}")
        return os.path.join(self.models_dir, self.MODEL_FILES[model_name][0])
    
    def is_model_downloaded(self, model_name):
        """Проверяем наличие файлов модели на диске"""
        try:
            model_path = self.get_model_path(model_name)
            exists = os.path.exists(model_path)
            print(f"Проверка модели {model_name} в {model_path}: {'найдена' if exists else 'не найдена'}", flush=True)
            return exists
        except Exception as e:
            print(f"Ошибка при проверке модели {model_name}: {e}", flush=True)
            return False
    
    def download_model(self, model_name):
        """Скачиваем модель, если её нет"""
        try:
            if not self.is_model_downloaded(model_name):
                print(f"Скачивание модели {model_name}...", flush=True)
                os.environ["WHISPER_MODEL_DIR"] = self.models_dir
                # Только скачиваем модель
                whisper.load_model(model_name, download_root=self.models_dir)
                print(f"Модель {model_name} успешно скачана", flush=True)
            return True
        except Exception as e:
            print(f"Ошибка скачивания модели {model_name}: {e}", flush=True)
            return False
    
    def load_model(self, model_name):
        """Загружаем модель в память"""
        try:
            if not self.is_model_downloaded(model_name):
                raise ValueError(f"Модель {model_name} не найдена. Сначала скачайте её.")
            
            if self.current_model_name != model_name:
                print(f"Загрузка модели {model_name} в память...", flush=True)
                self.model = whisper.load_model(model_name, download_root=self.models_dir)
                self.current_model_name = model_name
                print(f"Модель {model_name} загружена в память", flush=True)
            return True
        except Exception as e:
            print(f"Ошибка загрузки модели {model_name} в память: {e}", flush=True)
            return False
    
    def transcribe_audio(self, audio_data, language="ru"):
        if self.model is None or self.current_model_name is None:
            raise ValueError("Модель не загружена в память")
            
        try:
            result = self.model.transcribe(audio_data, language=language)
            return result["text"]
        except Exception as e:
            print(f"Ошибка распознавания: {e}", flush=True)
            raise 