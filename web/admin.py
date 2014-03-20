from django import forms
from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm


from easy_maps.widgets import AddressWithMapWidget


#import reversion

from web.models import *

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'organisation', 'first_name', 'last_name', 'mobile','is_active', 'date_joined', 'last_login', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'last_login')
    search_fields =	  ('email', 'first_name', 'last_name', 'username','organisation__name')
    list_display_links = ('email', 'username')
    form = CustomUserChangeForm

class LocationAdmin(admin.ModelAdmin):
    class form(forms.ModelForm):
        class Meta:
            widgets = {
                'address': AddressWithMapWidget({'class': 'vTextField'})
            }



class LocationInline(admin.TabularInline):
    model           = Location


class InstrumentInline(admin.TabularInline):
    model           = Instrument




#class OrgAdmin(reversion.VersionAdmin):
class OrgAdmin(admin.ModelAdmin):

    class Meta:
		model = Organisation

    list_display = ('name','org_type')
    search_fields =	 ('name',)
    inlines = [LocationInline, InstrumentInline]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Organisation, OrgAdmin)
admin.site.register(Location, LocationAdmin)