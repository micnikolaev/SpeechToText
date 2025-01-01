# Speech To Text

Веб-приложение для перевода аудио в текст с возможностью исправления и анализа текста через AI.

## Возможности
- Распознавание русской речи из WAV файлов
- Три модели на выбор (полная 1.8GB, средняя 2.5GB, легкая 45MB)
- AI-коррекция распознанного текста
- Создание краткого описания текста
- Веб-интерфейс для загрузки и обработки файлов

## Требования

### Системные требования
- Python 3.9+
- Минимум 8GB свободного места для моделей

### Установка системных зависимостей

1. FFmpeg:
```bash
# MacOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
choco install ffmpeg
```

2. Ollama:
```bash
# MacOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows - посетите https://ollama.com/download
```

### Модели распознавания речи
Модели загружаются автоматически при первом запуске. Доступные модели:
- Полная (1.8GB): vosk-model-ru-0.42
- Средняя (2.5GB): vosk-model-ru-0.10
- Легкая (45MB): vosk-model-small-ru-0.22

### AI модель
При первом запуске будет автоматически загружена модель t-lite для Ollama.

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd SpeechToText
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
```

3. Активируйте окружение:
```bash
# Windows
venv\Scripts\activate
# Linux/MacOS
source venv/bin/activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Запустите сервер:
```bash
python server.py
```

3. Откройте в браузере:
```
http://127.0.0.1:5000
```

## Использование

1. Выберите модель распознавания
2. Загрузите WAV файл
3. Опционально включите AI-коррекцию
4. Нажмите "Перевести в текст"
5. После получения текста можно создать его краткое описание