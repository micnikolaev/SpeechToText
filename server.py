from flask import Flask, send_file, request, jsonify
import requests
from vosk import Model, KaldiRecognizer
import subprocess
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

def resample_audio(input_path, output_path, target_sr=16000):
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
        logging.error(f"FFmpeg error: {e.stderr.decode()}")
        return False

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
    resampled_path = "resampled_audio.wav"
    use_ai = request.form.get('useAI') == "true"
    
    try:
        audio_file.save(temp_path)
        
        if not resample_audio(temp_path, resampled_path):
            return jsonify({'error': 'Failed to resample audio'}), 500
        
        model = Model(str(MODEL_PATH / MODELS[model_type]['path']))
        
        with wave.open(resampled_path, 'rb') as wf:
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
                
            complete_text = ' '.join(full_text).strip()
            if use_ai and complete_text:
                complete_text = ollama.process_text(complete_text)
            return jsonify({'text': complete_text or 'Текст не распознан'})
            
    except Exception as e:
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': str(e)}), 500
        
    finally:
        for path in [temp_path, resampled_path]:
            if os.path.exists(path):
                os.remove(path)

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        text = request.json.get('text')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        summary = ollama.summarize_text(text)
        return jsonify({'summary': summary})
    except Exception as e:
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': str(e)}), 500

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