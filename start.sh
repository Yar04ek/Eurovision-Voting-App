# 1. Активировать виртуальное окружение
if [ -d "eurovision_venv" ]; then
  source eurovision_venv/bin/activate
else
  echo "Виртуальное окружение eurovision_venv не найдено, создаю..."
  python3 -m venv eurovision_venv
  source eurovision_venv/bin/activate
  pip install -r requirements.txt
fi

# 2. Экспорт переменных из .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# 3. Применить миграции и сидирование
flask db upgrade
flask seed-artists

# 4. Запустить сервер
exec flask run --host=0.0.0.0 --port=5000