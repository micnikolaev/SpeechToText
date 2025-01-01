# SpeechToText

Веб-приложение для транскрибации аудио в текст.

## Возможности
- Распознавание русской речи из WAV файлов  
- Выбор между полной и легкой моделями
- Веб-интерфейс для загрузки файлов

## Подготовка окружения

1. Создание виртуального окружения:
```bash
python -m venv venv
```

2. Активация окружения:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/MacOS:
```bash
source venv/bin/activate
```

3. Установка зависимостей:
```bash
pip install flask requests
```

## Запуск
```bash
python app.py
```
Приложение будет доступно по адресу http://localhost:5000

## Технологии
- Flask
- JavaScript