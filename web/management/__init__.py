

from django.db.models.signals import post_syncdb
from django.db.models import signals
from django.conf import settings
from django.utils.translation import ugettext_noop as _

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("booking_requested", _("New Booking Requested"), _("New Booking Requested"))
        notification.create_notice_type("tuner_request", _("Can you tune?"), _("Can you tune?"))

    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"


from web.management.test_data import *


signals.post_syncdb.disconnect(
    create_superuser,
    sender=auth_app,
    dispatch_uid = "django.contrib.auth.management.create_superuser"
)

def add_initial_data(sender, **kwargs):

    # add system user
    try:
        User.objects.get(username='pbright')
    except User.DoesNotExist:


        pb = User.objects.create_superuser('pbright','phoebebright@spamcop.net','irnbru')
        pb.first_name = "Phoebe"
        pb.last_name = "Bright"
        pb.save()

        sys = User.objects.create('system','system@tunemypiano.com','system')
        sys.first_name = "System"
        sys.last_name = "User"
        sys.save()



post_syncdb.connect(add_initial_data)



