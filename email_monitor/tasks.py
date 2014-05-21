from email_monitor.models import Monitor

from datetime import timedelta
import imaplib

from celery import task

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


@task
def send(*args, **kwargs):
    Monitor.send()

@task
def check(*args, **kwargs):
    Monitor.check()

