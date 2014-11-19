from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext
from django.template.loader import find_template
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from notification import backends


from django_twilio.client import twilio_client

from web.models import PhoneNumber

import os.path


class TwilioBackend(backends.BaseBackend):
    spam_sensitivity = 2

    def can_send(self, user, notice_type):
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

            #if this is a booking, use the phone number associated with it
            if booking:
                number = booking.get_sms_number()
            else:
                number = settings.DEFAULT_FROM_SMS


            print "sending twillio ", recipient, recipient.mobile, "from ", number

            m = twilio_client.messages.create(
                to=recipient.mobile,
                from_=number,
                body=sms,
                status_callback="http://%s/%s/%s/" % (settings.TWILIO_CALLBACK_DOMAIN, "sms_callback", booking.ref),
                )



            print m.sid
            print m.status

            Log.objects.create(notice_type = notice_type,
                                   method='sms',
                                   recipient = recipient,
                                   subject=sms,
                                   booking=booking)


@csrf_exempt
def sms_callback(request, ref):
    #TODO: need to match this to call and save in db
    print "SMS_CALLBACK for ref ------", ref
    #print request._post.get('MessageSid'),request._post.get('MessageStatus')
    #print request._post.get('SmsSid'),request._post.get('SmsStatus')
    print request.POST

    return HttpResponse("OK")