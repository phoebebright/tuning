from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext
from django.template.loader import find_template

from notification import backends


from django_twilio_sms.utils import send_sms

import os.path


class TwilioBackend(backends.BaseBackend):
    spam_sensitivity = 2

    def can_send(self, user, notice_type):
        print "twillio can_send ",user, user.use_sms , user.mobile
        return user.use_sms and user.mobile


    def deliver(self, recipient, sender, notice_type, extra_context):

        from notification.models import Log

        template = "%s/%s/sms.txt" % (settings.NOTIFICATION_TEMPLATES, notice_type)
        # only send sms if an sms.txt template exists
        if os.path.isfile(template):


            context = self.default_context()
            context.update(extra_context)

            try:
                booking=extra_context['booking']
            except:
                booking = None

            messages = self.get_formatted_messages((
                "sms.txt",
            ), notice_type.label, context)

            sms = "".join(render_to_string(template, {}, context).splitlines())

            print "sending twillio ", recipient, recipient.mobile
            result = send_sms(None, recipient.mobile, sms)
            print result

            Log.objects.create(notice_type = notice_type,
                                   method='sms',
                                   recipient = recipient,
                                   subject=sms,
                                   booking=booking)