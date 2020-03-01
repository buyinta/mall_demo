from celery import Celery
import os

if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mall_demo.settings.dev'

# celery -A celery_tasks.main worker --pool=solo -l info
celery_app = Celery('mall_demo')
celery_app.config_from_object('celery_tasks.config')
celery_app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])
