python manage.py collectstatic --no-input
python manage.py migrate
python manage.py createsuperuser --no-input
gunicorn django_ocr_service.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 -t 300 --log-level INFO