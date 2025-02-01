# Speech To Text

![Демонстрация](demo.gif)

## Возможности
- Распознавание русской речи из WAV файлов
- Три модели на выбор (полная 1.8GB, средняя 2.5GB, легкая 45MB)
- AI-коррекция распознанного текста
- Создание краткого описания текста

## Требования

### Системные требования
- Python 3.9+
- Минимум 15GB свободного места для моделей (включая Whisper large-v3)
- Рекомендуется наличие GPU для быстрой работы Whisper

### Установка системных зависимостей

#### 1. FFmpeg:

##### MacOS
```bash
brew install ffmpeg
```

##### Ubuntu/Debian
```bash
sudo apt-get install ffmpeg
```

##### Windows
```bash
choco install ffmpeg
```

#### 2. Ollama:

##### MacOS
```bash
brew install ollama
```

##### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

##### Windows
```bash
Посетите https://ollama.com/download
```

### Модели распознавания речи
Модели загружаются автоматически при первом запуске. Доступные модели:

#### Vosk модели:
- Полная (1.8GB): vosk-model-ru-0.42
- Средняя (2.5GB): vosk-model-ru-0.10
- Легкая (45MB): vosk-model-small-ru-0.22

#### Whisper модель:
- Large-v3 (~6GB): Наиболее точная модель для распознавания речи
  - Поддерживает множество языков
  - Высокая точность распознавания
  - Требует больше вычислительных ресурсов

### AI модель
При первом запуске будет автоматически загружена модель t-lite для Ollama.

## Установка

#### 1. Клонируйте и перейдите в репозитоий репозиторий:
```bash
git clone https://github.com/micnikolaev/SpeechToText.git
cd SpeechToText
```

#### 2. Создайте виртуальное окружение:
```bash
python -m venv venv
```

#### 3. Активируйте окружение:

##### Windows
```bash
venv\Scripts\activate
```

##### Linux/MacOS
```bash
source venv/bin/activate
```

#### 4. Установите зависимости:
```bash
pip install -r requirements.txt
```

#### 5. Запустите сервер:

##### Вариант 1: Прямой запуск через Python
```bash
python server.py
```

##### Вариант 2: Для MacOS/Linux можно использовать скрипт запуска

Сначала сделайте скрипт исполняемым:
```bash
chmod +x start_server.command
```

Затем запустите двойным кликом или через терминал:
```bash
./start_server.command
```

#### 6. Откройте в браузере:

[http://127.0.0.1:5001](http://127.0.0.1:5001)

## Использование

1. Выберите модель распознавания
2. Загрузите WAV файл
3. Опционально включите AI-коррекцию
4. Нажмите "Перевести в текст"
5. После получения текста можно создать его краткое описание