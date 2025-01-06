from flask import Flask, send_file, request, jsonify
import os
from vosk_service import VoskService
from ollama_service import OllamaService
import subprocess

app = Flask(__name__)
import logging
logging.basicConfig(level=logging.INFO)

vosk_service = VoskService()
ollama = OllamaService()

@app.route('/')
def home():
    return send_file('index.html')

def convert_to_wav(input_path, output_path):
    """
    Конвертирует аудио/видео в WAV формат
    Поддерживает: mp4, avi, mov, mkv, mp3, m4a, etc.
    """
    try:
        subprocess.run([
            'ffmpeg', '-i', input_path,
            '-vn',  # пропускаем видеопоток
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y', output_path
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка конвертации: {str(e)}")
        return False

@app.route('/transcribe', methods=['POST'])
def transcribe():
    app.logger.info('Starting transcription')
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    model_type = request.form.get('model', 'full')
    if model_type not in vosk_service.MODELS:
        return jsonify({'error': 'Invalid model type'}), 400
        
    audio_file = request.files['audio']
    original_path = "original_audio"  # Сохраняем с оригинальным расширением
    temp_path = "temp_audio.wav"
    
    try:
        # Сохраняем оригинальный файл
        audio_file.save(original_path)
        
        # Конвертируем в WAV с нужными параметрами
        if not convert_to_wav(original_path, temp_path):
            return jsonify({'error': 'Failed to convert audio to WAV'}), 500
            
        # Транскрибируем
        complete_text = vosk_service.transcribe_audio(temp_path, model_type)
        
        # Обработка через AI если требуется
        ollama_model = request.form.get('ollama_model')
        use_ai = request.form.get('useAI') == "true"
        if use_ai and complete_text:
            complete_text = ollama.process_text(complete_text, model_name=ollama_model)
            
        return jsonify({'text': complete_text})
            
    except Exception as e:
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Очистка временных файлов
        for path in [original_path, temp_path]:
            if os.path.exists(path):
                os.remove(path)

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        text = request.json.get('text')
        model = request.json.get('model')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        summary = ollama.summarize_text(text, model_name=model)
        return jsonify({'summary': summary})
    except Exception as e:
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        text = data.get('text')
        question = data.get('question')
        model = data.get('model')
        
        if not text or not question:
            return jsonify({'error': 'No text or question provided'}), 400
            
        answer = ollama.answer_question(text, question, model_name=model)
        return jsonify({'answer': answer})
    except Exception as e:
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/check_model', methods=['POST'])
def check_model():
    try:
        model = request.json.get('model')
        if not model:
            return jsonify({'error': 'No model specified'}), 400
            
        if model in ollama.loaded_models:
            return jsonify({'status': 'ready'})
            
        if ollama.load_model(model):
            return jsonify({'status': 'ready'})
        else:
            return jsonify({'status': 'error'})
    except Exception as e:
        app.logger.error(f'Error checking model: {str(e)}')
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