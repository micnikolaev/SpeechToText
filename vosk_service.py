from pathlib import Path
import requests
import zipfile
import wave
import json
import logging
import subprocess
from vosk import Model, KaldiRecognizer
import os

class VoskService:
    MODELS = {
        'full': {
            'url': "https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip",
            'path': "vosk-model-ru-0.42"
        },
        'medium': {
            'url': "https://alphacephei.com/vosk/models/vosk-model-ru-0.10.zip",
            'path': "vosk-model-ru-0.10"
        },
        'small': {
            'url': "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip",
            'path': "vosk-model-small-ru-0.22"
        }
    }

    def __init__(self, models_dir="models"):
        self.model_path = Path(models_dir)
        self.logger = logging.getLogger(__name__)
        self.current_model = None
        self.current_model_type = None

    def download_model(self, model_type='full'):
        """Загружает модель указанного размера, если она еще не загружена"""
        model_info = self.MODELS[model_type]
        model_dir = self.model_path / model_info['path']
        
        if not model_dir.exists():
            self.logger.info(f"Downloading {model_type} model...")
            self.model_path.mkdir(exist_ok=True)
            
            response = requests.get(model_info['url'], stream=True)
            response.raise_for_status()
            zip_path = self.model_path / f"{model_info['path']}.zip"
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            self.logger.info("Extracting model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.model_path)
            
            zip_path.unlink()
            self.logger.info("Model ready")

    def resample_audio(self, input_path, output_path, target_sr=16000):
        """Пересэмплирует аудио в формат, необходимый для Vosk"""
        try:
            subprocess.run([
                'ffmpeg', '-i', input_path,
                '-ar', str(target_sr),
                '-ac', '1',
                '-y',
                output_path
            ], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg error: {e.stderr.decode()}")
            return False

    def load_model(self, model_type='full'):
        """Загружает модель в память"""
        if self.current_model_type != model_type:
            model_info = self.MODELS[model_type]
            model_path = str(self.model_path / model_info['path'])
            self.current_model = Model(model_path)
            self.current_model_type = model_type
        return self.current_model

    def transcribe_audio(self, audio_path, model_type='full'):
        """Транскрибирует аудио файл в текст"""
        try:
            model = self.load_model(model_type)
            
            with wave.open(audio_path, 'rb') as wf:
                rec = KaldiRecognizer(model, 16000)
                full_text = []
                
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        if result.get('text'):
                            full_text.append(result['text'])
                
                final_result = rec.FinalResult()
                final_text = json.loads(final_result).get('text', '')
                if final_text:
                    full_text.append(final_text)
                    
                return ' '.join(full_text).strip() or 'Текст не распознан'
                
        except Exception as e:
            self.logger.error(f'Transcription error: {str(e)}')
            raise