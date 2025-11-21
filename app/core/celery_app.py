from celery import Celery
from app.config import settings
from typing import Optional
import logging

celery_app = Celery(
    "paragraph_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.dictionary_tasks"]
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  
    task_soft_time_limit=240, 
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

