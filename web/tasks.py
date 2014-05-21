from web.models import Booking

from datetime import timedelta
import imaplib

from celery import task

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


@task
def check_bookings():
    logger.info('Checking for tunings that should be complete by now')
    print 'Checking start'
    Booking.check_to_complete()
    logger.info('Checking end')

@task
def celery_ping():
    print "Pinged"
    logger.info("pinged")

