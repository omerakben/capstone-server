web: gunicorn deadline_api.wsgi:application --bind 0.0.0.0:$PORT --workers 2
release: python manage.py migrate && python manage.py seed_demo_data
