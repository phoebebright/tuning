from email_monitor.models import Monitor
from django.contrib import admin


class MonitorAdmin(admin.ModelAdmin):
    list_display = ('id', 'sent', 'received', 'seconds')


admin.site.register(Monitor, MonitorAdmin)

