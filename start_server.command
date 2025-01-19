#!/bin/bash

# Переходим в директорию скрипта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем сервер
python server.py

# Ждем нажатия клавиши перед закрытием окна
read -p "Press any key to continue..." 