#!/bin/bash

# Переходим в директорию скрипта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
pip3.10 install -r requirements.txt

# Запускаем сервер
python3.10 server.py

# Ждем нажатия клавиши перед закрытием окна
read -p "Press any key to continue..." 