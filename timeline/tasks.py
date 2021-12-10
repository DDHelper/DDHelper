from celery import shared_task
from celery.utils.log import get_task_logger
import logging

logger: logging.Logger = get_task_logger(__name__)


@shared_task
def process_timeline(dynamic_id):
    pass

