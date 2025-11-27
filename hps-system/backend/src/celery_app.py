"""
Configuración de Celery para tareas asíncronas
"""
import os
from celery import Celery
from src.config.settings import settings

# Obtener configuración

# Crear instancia de Celery
celery_app = Celery(
    "hps_system",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=[
        "src.tasks.email_tasks",
        "src.tasks.analysis_tasks"
    ]
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hora
    task_routes={
        "src.tasks.email_tasks.*": {"queue": "email"},
        "src.tasks.analysis_tasks.*": {"queue": "analysis"},
    },
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "email": {
            "exchange": "email",
            "routing_key": "email",
        },
        "analysis": {
            "exchange": "analysis", 
            "routing_key": "analysis",
        },
    }
)

# Configuración de logging
celery_app.conf.update(
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)

if __name__ == "__main__":
    celery_app.start()
