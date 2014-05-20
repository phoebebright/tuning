
import imaplib
# import poplib


from django.core.mail import send_mail
from django.conf import settings

from web.models import TunerCall, BOOKING_REQUESTED

from exceptions import GettingMailError

"""MailBox class for processing IMAP email.

(To use with Gmail: enable IMAP access in your Google account settings)

usage with GMail:

    import mailbox

    with mailbox.MailBox(gmail_username, gmail_password) as mbox:
        print mbox.get_count()
        print mbox.print_msgs()


for other IMAP servers, adjust settings as necessary.
"""


import imaplib
import time
import uuid
from email import email



IMAP_SERVER = 'mail.tunemypiano.co.uk'
IMAP_PORT = '993'
IMAP_USE_SSL = False



class MailBox(object):

    def __init__(self, user, password):
        self.user = user
        self.password = password
        if IMAP_USE_SSL:
            self.imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        else:
            self.imap = imaplib.IMAP4(IMAP_SERVER)

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

    def print_msgs(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'ALL')
        for num in reversed(data[0].split()):
            status, data = self.imap.fetch(num, '(RFC822)')
            print 'Message %s\n%s\n' % (num, data[0][1])

    def get_latest_email_sent_to(self, email_address, timeout=300, poll=1):
        start_time = time.time()
        while ((time.time() - start_time) < timeout):
            # It's no use continuing until we've successfully selected
            # the inbox. And if we don't select it on each iteration
            # before searching, we get intermittent failures.
            status, data = self.imap.select('Inbox')
            if status != 'OK':
                time.sleep(poll)
                continue
            status, data = self.imap.search(None, 'TO', email_address)
            data = [d for d in data if d is not None]
            if status == 'OK' and data:
                for num in reversed(data[0].split()):
                    status, data = self.imap.fetch(num, '(RFC822)')
                    email_msg = email.message_from_string(data[0][1])
                    return email_msg
            time.sleep(poll)
        raise AssertionError("No email sent to '%s' found in inbox "
             "after polling for %s seconds." % (email_address, timeout))

    def delete_msgs_sent_to(self, email_address):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'TO', email_address)
        if status == 'OK':
            for num in reversed(data[0].split()):
                status, data = self.imap.fetch(num, '(RFC822)')
                self.imap.store(num, '+FLAGS', r'\Deleted')
        self.imap.expunge()


def read_system_email(request):

   with MailBox("system@tunemypiano.co.uk", "Hg76bbqq") as mbox:
        print mbox.get_count()
        print mbox.print_msgs()



def send_requests(request=None):

    # check and remove calls for bookings with deadline in the past
    expire_overdue_calls()


    for item in TunerCall.objects.unsent():


        # don't send message if booking already has a tuner or no tuner
        if item.booking.status > BOOKING_REQUESTED:
            item.expire()
        elif not item.tuner:
            item.expire()
        else:

            subject = "Are you available for %s?" % (item.booking.short_description)
            body = """See full details: %s

            Reply with Yes or No in the subject line.""" % (item.booking.get_absolute_url())

            name, domain = settings.DEFAULT_FROM_EMAIL.split('@')
            from_email = "%s+%s@%s" % (name, item.booking.ref, domain)

            to_email = "phoebebright310+b_%s@gmail.com" % ( item.booking.ref)

            print "sending email to "+to_email
            send_mail(subject, body, from_email, [to_email,], fail_silently=True)


def expire_overdue_calls(request=None):
    #TODO: only allow system user or admin to run

    for item in TunerCall.objects.overdue():
        pass
        #TODO: is selecting all records
        #item.expire()
