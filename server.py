from flask import Flask, send_file, request, jsonify, send_from_directory
from vosk import Model, KaldiRecognizer
import requests
import wave
import os
from pathlib import Path
import zipfile
import json
from ollama_service import OllamaService

app = Flask(__name__)
import logging
logging.basicConfig(level=logging.INFO)

ollama = OllamaService()

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

MODEL_PATH = Path("models")

def download_model(model_type='full'):
    model_info = MODELS[model_type]
    model_dir = MODEL_PATH / model_info['path']
    
    if not model_dir.exists():
        print(f"Downloading {model_type} model...")
        MODEL_PATH.mkdir(exist_ok=True)
        
        response = requests.get(model_info['url'], stream=True)
        response.raise_for_status()
        zip_path = MODEL_PATH / f"{model_info['path']}.zip"
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print("Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(MODEL_PATH)
        
        zip_path.unlink()
        print("Model ready")

@app.route('/')
def home():
    return send_file('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    app.logger.info('Starting transcription')
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    model_type = request.form.get('model', 'full')
    if model_type not in MODELS:
        return jsonify({'error': 'Invalid model type'}), 400
        
    audio_file = request.files['audio']
    temp_path = "temp_audio.wav"
    
    try:
        audio_file.save(temp_path)
        model = Model(str(MODEL_PATH / MODELS[model_type]['path']))
        
        with wave.open(temp_path, 'rb') as wf:
            rec = KaldiRecognizer(model, wf.getframerate())
            
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
                
            complete_text = ' '.join(full_text).strip()
            if complete_text:
                complete_text = ollama.process_text(complete_text)
            return jsonify({'text': complete_text or 'Текст не распознан'})
            
    except Exception as e:
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': str(e)}), 500
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    print("Starting server...")
    try:
        download_model('full')
        download_model('medium')
        download_model('small')
        print("Starting Ollama...")
        if ollama.start():
            print("Starting server on http://localhost:5000")
            app.run(port=5000)
        else:
            print("Failed to start Ollama")
    except Exception as e:
        print(f"Error: {e}")