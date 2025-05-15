import os
from os import environ as env
from dotenv import load_dotenv
from celery import Celery


load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth.settings')

app = Celery('auth')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.broker_url = env['REDIS_URL']