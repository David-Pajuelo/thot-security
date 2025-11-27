import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cryptotrace_backend.settings")

app = Celery("cryptotrace_backend")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Celery debug task ejecutada: {self.request!r}")

