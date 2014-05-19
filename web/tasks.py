from web.models import Booking

from datetime import timedelta
import imaplib

from celery import task

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


@task
def check_bookings(a=None,b=None):
    logger.info('Checking for tunings that should be complete')
    print 'Checking'
    Booking.check_to_complete()
    logger.info('Checking')

@task
def celery_ping(a=None,b=None):
    print "Pinged"
    logger.info("pinged")

