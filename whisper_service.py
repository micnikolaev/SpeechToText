import whisper
import numpy as np
from typing import Optional
import logging

class WhisperService:
    def __init__(self, model_name: str = "large-v3"):
        """
        Инициализация Whisper сервиса
        
        Args:
            model_name: Название модели Whisper ("tiny", "base", "small", "medium", "large-v3")
            По умолчанию используется large-v3 как наиболее точная модель
        """
        print(f"Загрузка Whisper модели {model_name}...")
        self.model = whisper.load_model(model_name)
        print("Whisper модель загружена успешно")
    
    def transcribe_audio(self, audio_data: np.ndarray, language: Optional[str] = None) -> str:
        """
        Преобразование аудио в текст
        
        Args:
            audio_data: Аудио данные в формате numpy array
            language: Код языка (например, "ru" для русского)
            
        Returns:
            Распознанный текст
        """
        try:
            print("\n=== Характеристики аудио файла ===")
            print(f"Тип данных: {audio_data.dtype}")
            print(f"Размер массива: {audio_data.shape}")
            print(f"Длительность (сек): {len(audio_data) / 16000:.2f}")  # Assuming 16kHz
            print(f"Минимальное значение: {audio_data.min():.6f}")
            print(f"Максимальное значение: {audio_data.max():.6f}")
            print(f"Среднее значение: {audio_data.mean():.6f}")
            print(f"Стандартное отклонение: {audio_data.std():.6f}")
            print(f"Количество нулевых значений: {np.sum(audio_data == 0)}")
            print(f"Количество значений > 1: {np.sum(np.abs(audio_data) > 1)}")
            print("================================\n")
            
            if len(audio_data) == 0:
                raise ValueError("Пустые входные данные")
            
            # Нормализация аудио данных
            audio_data = audio_data.astype(np.float32)
            max_value = np.abs(audio_data).max()
            
            if max_value > 1.0:
                print(f"Нормализация аудио. Максимальное значение до: {max_value}")
                audio_data = audio_data / max_value
                print(f"Максимальное значение после: {np.abs(audio_data).max()}")
            
            print("Начинаем транскрибацию...", flush=True)
            result = self.model.transcribe(
                audio_data,
                language="ru" if language is None else language,
                task="transcribe",
                best_of=5
            )
            
            text = result["text"].strip()
            print(f"Транскрибация успешно завершена. Длина текста: {len(text)} символов")
            return text
        
        except Exception as e:
            print(f"Ошибка при транскрибации через Whisper: {str(e)}", flush=True)
            import traceback
            print(traceback.format_exc(), flush=True)
            raise 