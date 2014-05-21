from datetime import datetime

from django.db import models
from django.conf import settings
from django.core.mail import send_mail


import imaplib
from email import email



MONITOR_FROM_EMAIL = getattr(settings, "MONITOR_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL)
MONITOR_TO_EMAIL = getattr(settings, "MONITOR_TO_EMAIL", settings.DEFAULT_FROM_EMAIL)


MONITOR_IMAP_SERVER = getattr(settings, "MONITOR_IMAP_SERVER", None)
MONITOR_IMAP_PORT = getattr(settings, "MONITOR_IMAP_PORT", '993')
MONITOR_IMAP_USE_SSL = getattr(settings, "MONITOR_IMAP_USE_SSL", False)
MONITOR_IMAP_PASSWORD = getattr(settings, "MONITOR_IMAP_PASSWORD", None)

SUBJECT_LINE = "Email Monitor Check Mail"

assert MONITOR_IMAP_SERVER and MONITOR_IMAP_PASSWORD, "Add MONITOR_IMAP_SERVER and MONITOR_IMAP_PASSwORD to settings.py"



class Monitor(models.Model):
    sent = models.DateTimeField(auto_now_add=True)
    received = models.DateTimeField(blank=True, null=True)
    seconds = models.PositiveSmallIntegerField(blank=True, null=True)


    def __str__(self):
        if self.seconds:
            return "%s Roundtrip = %s seconds" % (self.sent, self.seconds)
        else:
            return "Sent at %s" % (self.sent,)


    @classmethod
    def send(cls):

        assert settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend', \
            "Monitor can't work when using the console backend. Try using 'django.core.mail.backends.smtp.EmailBackend'"

        new = cls.objects.create()
        x = send_mail(SUBJECT_LINE, "Ref %s" % new.id, MONITOR_FROM_EMAIL, [MONITOR_TO_EMAIL,])
        if x:
            pass


    @classmethod
    def check(cls):

        with MailBox(MONITOR_TO_EMAIL, MONITOR_IMAP_PASSWORD) as mbox:
            msgs = mbox.get_msgs()

            for item in msgs:

                body = email.message_from_string(msgs[0][1])
                print body


    @classmethod
    def match(cls, id):
            try:
                matched = cls.objects.get(id=id, received__isnull=True)
                matched.received = datetime.now()
                seconds = (matched.received - matched.sent).seconds
                matched.save()
            except cls.DoesNotExist:
                print "Email Monitor unable to match id %s"  % id
                pass




class MailBox(object):

    def __init__(self, user, password):
        self.user = user
        self.password = password
        if MONITOR_IMAP_USE_SSL:
            self.imap = imaplib.IMAP4_SSL(MONITOR_IMAP_SERVER, MONITOR_IMAP_PORT)
        else:
            self.imap = imaplib.IMAP4(MONITOR_IMAP_SERVER)

    def __enter__(self):
        self.imap.login(self.user, self.password)
        return self

    def __exit__(self, type, value, traceback):
        self.imap.close()
        self.imap.logout()

    def get_count(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'ALL')
        return sum(1 for num in data[0].split())

    def get_msgs(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'ALL')

        msgs = []
        for num in reversed(data[0].split()):
            #status, data = self.imap.fetch(num, '(RFC822)')
            status, data = self.imap.search(None, '(SUBJECT "%s")' % SUBJECT_LINE)
            if status == 'OK':
                msgs.append(data)

        return msgs

    def fetch_message(self, num):
        self.imap.select('Inbox')
        status, data = self.imap.fetch(str(num), '(RFC822)')
        email_msg = email.message_from_string(data[0][1])
        return email_msg

    def delete_message(self, num):
        self.imap.select('Inbox')
        self.imap.store(num, '+FLAGS', r'\Deleted')
        self.imap.expunge()

    def delete_all(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'ALL')
        for num in data[0].split():
            self.imap.store(num, '+FLAGS', r'\Deleted')
        self.imap.expunge()


