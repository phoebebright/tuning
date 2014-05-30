from email_monitor.models import Monitor

from datetime import timedelta
import imaplib

from celery import task

from celery.utils.log import get_task_logger
logger = get_task_logger('celery')


@task(name='send-email')
def send(sender, subject, body):

   logger.info('Checking for emails to send')

   for email in EmailLog.objects.filter(date_sent__isnull = True):
        logger.info('Sending email to %s' % email.to_email)
        print "sending email"
        email.send()

@task
def check(*args, **kwargs):
    Monitor.check()

