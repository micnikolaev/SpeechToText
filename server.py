from flask import Flask, send_file, request, jsonify
import os
from vosk_service import VoskService
from ollama_service import OllamaService

app = Flask(__name__)
import logging
logging.basicConfig(level=logging.INFO)

vosk_service = VoskService()
ollama = OllamaService()

@app.route('/')
def home():
    return send_file('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    app.logger.info('Starting transcription')
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    model_type = request.form.get('model', 'full')
    if model_type not in vosk_service.MODELS:
        return jsonify({'error': 'Invalid model type'}), 400
        
    audio_file = request.files['audio']
    temp_path = "temp_audio.wav"
    resampled_path = "resampled_audio.wav"
    use_ai = request.form.get('useAI') == "true"
    
    try:
        audio_file.save(temp_path)
        
        if not vosk_service.resample_audio(temp_path, resampled_path):
            return jsonify({'error': 'Failed to resample audio'}), 500
        
        complete_text = vosk_service.transcribe_audio(resampled_path, model_type)
        
        if use_ai and complete_text:
            complete_text = ollama.process_text(complete_text)
            
        return jsonify({'text': complete_text})
            
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
        # Предзагрузка всех моделей
        for model_type in vosk_service.MODELS:
            vosk_service.download_model(model_type)
            
        print("Starting Ollama...")
        if ollama.start():
            print("Starting server on http://localhost:5000")
            app.run(port=5000)
        else:
            print("Failed to start Ollama")
    except Exception as e:
        print(f"Error: {e}")