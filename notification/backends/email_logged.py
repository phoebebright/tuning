from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext

from notification import backends



class EmailLoggedBackend(backends.BaseBackend):
    spam_sensitivity = 2

    def can_send(self, user, notice_type):

        if not user.email:
            print "No email address for user %s so can't send notification" % user
            return False

        return True
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




        # add to log file
        email = EmailLog.objects.create(
               from_email = sender.email,
               recipient = recipient,
               subject = subject,
               body = body,
        )
        print 'about to send email just added'
        email.send_now()

