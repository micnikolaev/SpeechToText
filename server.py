from flask import Flask, send_file, request, jsonify
from flask_cors import CORS  # Добавляем импорт CORS
import os
from vosk_service import VoskService
from ollama_service import OllamaService
import subprocess
import webbrowser
from whisper_service import WhisperService
import numpy as np
import json
import websockets
import logging
import signal
import sys
import time
from werkzeug.serving import make_server
import threading
import asyncio

app = Flask(__name__)
CORS(app)  # Включаем CORS для всех маршрутов
logging.basicConfig(level=logging.INFO)

vosk_service = VoskService()
ollama = OllamaService()
whisper_service = WhisperService("large-v3")

class SpeechRecognitionServer:
    def __init__(self):
        self.whisper_service = whisper_service
        self.vosk_service = vosk_service
        print("SpeechRecognitionServer инициализирован", flush=True)

    async def handle_websocket(self, websocket):
        client_id = id(websocket)
        print(f"Новое WebSocket соединение: {client_id}", flush=True)
        logging.info(f"Новое WebSocket соединение: {client_id}")
        
        try:
            # Получаем тип модели
            model_type = await websocket.recv()
            print(f"Клиент {client_id} выбрал модель: {model_type}", flush=True)
            
            if model_type == "whisper":
                print(f"Клиент {client_id} использует Whisper", flush=True)
                try:
                    # Получаем аудио данные
                    audio_data = await websocket.recv()
                    print(f"Получены аудио данные от клиента {client_id}, размер: {len(audio_data)} байт", flush=True)
                    
                    # Конвертируем bytes в numpy array
                    audio_np = np.frombuffer(audio_data, dtype=np.float32)
                    print(f"Аудио данные преобразованы в numpy array, размер: {audio_np.shape}", flush=True)
                    
                    if len(audio_np) == 0:
                        raise ValueError("Получены пустые аудио данные")
                    
                    # Распознаем текст через Whisper
                    text = self.whisper_service.transcribe_audio(audio_np, language="ru")
                    print(f"Результат распознавания для клиента {client_id}: {text[:100]}...", flush=True)
                    
                    try:
                        await websocket.send(text)
                        print(f"Результат отправлен клиенту {client_id}", flush=True)
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"Соединение закрыто при отправке результата: {e}", flush=True)
                        return
                    
                except Exception as e:
                    error_msg = f"Ошибка при транскрибации Whisper: {str(e)}"
                    print(f"Клиент {client_id}: {error_msg}", flush=True)
                    try:
                        await websocket.send(json.dumps({"error": error_msg}))
                    except:
                        print(f"Не удалось отправить сообщение об ошибке клиенту {client_id}", flush=True)
            else:
                # Обработка Vosk
                rec = self.vosk_service.create_recognizer()
                
                while True:
                    audio_chunk = await websocket.recv()
                    if audio_chunk == b"DONE":
                        break
                        
                    if rec.AcceptWaveform(audio_chunk):
                        result = rec.Result()
                        await websocket.send(result)
                
                # Отправляем финальный результат
                final_result = rec.FinalResult()
                await websocket.send(final_result)
                
        except Exception as e:
            print(f"Ошибка обработки соединения {client_id}: {e}", flush=True)
            try:
                if not websocket.closed:
                    await websocket.send(json.dumps({"error": str(e)}))
            except:
                print(f"Не удалось отправить сообщение об ошибке клиенту {client_id}", flush=True)
        finally:
            print(f"Соединение {client_id} закрыто", flush=True)

async def start_websocket_server():
    print("Запуск WebSocket сервера...", flush=True)
    async with websockets.serve(
        SpeechRecognitionServer().handle_websocket,
        "0.0.0.0",
        8765,
        max_size=100 * 1024 * 1024,  # Увеличиваем до 100MB
        ping_interval=None,  # Отключаем пинги
        ping_timeout=None,   # Отключаем таймаут пингов
    ) as websocket_server:
        print("WebSocket сервер запущен на ws://0.0.0.0:8765", flush=True)
        await asyncio.Future()

def run_websocket_server():
    print("Инициализация WebSocket сервера...", flush=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_websocket_server())
    except Exception as e:
        print(f"Ошибка запуска WebSocket сервера: {e}", flush=True)
        raise

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

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server('0.0.0.0', 5001, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print("Starting Flask server thread...", flush=True)
        self.srv.serve_forever()

    def shutdown(self):
        print("Shutting down Flask server...", flush=True)
        self.srv.shutdown()

def cleanup():
    print("\nЗавершение работы сервера...", flush=True)
    logging.info("Начало процесса завершения работы")
    
    # Останавливаем Flask сервер
    if hasattr(cleanup, 'server_thread'):
        logging.info("Останавливаем Flask сервер")
        cleanup.server_thread.shutdown()
        cleanup.server_thread.join()
        logging.info("Flask сервер остановлен")
    
    # Останавливаем Ollama
    try:
        logging.info("Останавливаем Ollama")
        subprocess.run(['killall', 'ollama'], timeout=5)
        logging.info("Ollama остановлен")
    except subprocess.SubprocessError as e:
        logging.error(f"Ошибка при остановке Ollama: {e}")
    
    # Очищаем временные файлы
    temp_files = ['original_audio', 'temp_audio.wav']
    for file in temp_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                logging.info(f"Удален временный файл: {file}")
            except Exception as e:
                logging.error(f"Ошибка при удалении {file}: {e}")
    
    print("Сервер успешно остановлен", flush=True)
    logging.info("Сервер успешно остановлен")
    sys.stdout.flush()
    sys.exit(0)

def signal_handler(signum, frame):
    print("\nПолучен сигнал завершения...", flush=True)
    cleanup()

if __name__ == '__main__':
    print("Starting server...", flush=True)
    try:
        # Предзагрузка всех моделей
        for model_type in vosk_service.MODELS:
            vosk_service.download_model(model_type)
            
        print("Starting Ollama...", flush=True)
        if ollama.start():
            # Запускаем WebSocket сервер в отдельном потоке
            websocket_thread = threading.Thread(target=run_websocket_server)
            websocket_thread.daemon = True
            websocket_thread.start()
            time.sleep(1)  # Даем время на запуск WebSocket сервера
            
            # Запускаем Flask сервер в отдельном потоке
            print("Starting Flask server on port 5001...", flush=True)
            flask_thread = ServerThread(app)
            flask_thread.daemon = True
            flask_thread.start()
            
            # Бесконечный цикл для поддержания работы серверов
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nПолучено прерывание клавиатуры", flush=True)
                cleanup()
            
        else:
            print("Failed to start Ollama", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        cleanup()