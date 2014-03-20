

from django.db.models.signals import post_syncdb
from django.db.models import signals


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

post_syncdb.connect(add_initial_data)



