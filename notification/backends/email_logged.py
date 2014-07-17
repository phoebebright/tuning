from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext

from notification import backends

from web.models import CustomUser


class EmailLoggedBackend(backends.BaseBackend):
    spam_sensitivity = 2

    def can_send(self, user, notice_type):

        # user is passed in as email address
        # if they are a registered user, check they are happy to receive email, otherwise allow


        return user.use_email




        # can_send = super(EmailLoggedBackend, self).can_send(user, notice_type)
        # if can_send and user.email:
        #     return True
        # return False

    def deliver(self, recipient, sender, notice_type, extra_context):
        # TODO: require this to be passed in extra_context
        from notification.models import EmailLog


        if sender == None:
            from web.models import system_user
            sender = system_user()


        context = self.default_context()
        context.update({
            "recipient": recipient,
            "sender": sender,
            "notice": ugettext(notice_type.display),
        })
        context.update(extra_context)

        messages = self.get_formatted_messages((
            "short.txt",
            "full.txt"
        ), notice_type.label, context)

        subject = "".join(render_to_string("notification/email_subject.txt", {
            "message": messages["short.txt"],
        }, context).splitlines())

        body = render_to_string("notification/email_body.txt", {
            "message": messages["full.txt"],
        }, context)



        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient.email])

        #TODO: if there is a booking in extra_context, then add to log
        #booking.log(comment,  type, user=None):