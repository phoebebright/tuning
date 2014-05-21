from django.conf.urls import patterns, url

from email_monitor.views import send, check

urlpatterns = patterns(
    "email_monitor.views",
    url(r"^send/$", 'send', name="send_email_to_monitor"),
    url(r"^check/$", 'check', name="check_for_sent_emails"),
)

