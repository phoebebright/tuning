from django import forms
from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from django.forms.widgets import TextInput

from django_google_maps.widgets import GoogleMapsAddressWidget
from django_google_maps.fields import AddressField, GeoLocationField


#import reversion

from web.models import *
#TODO: user admin is not working, can't get to second screen

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

    formfield_overrides = {
        AddressField: {'widget': GoogleMapsAddressWidget},
        GeoLocationField: {'widget': TextInput(attrs={'readonly': 'readonly'})},
                    }



class LocationInline(admin.TabularInline):
    model           = Location
    fields = ['name', ]


class InstrumentInline(admin.TabularInline):
    model           = Instrument




#class OrgAdmin(reversion.VersionAdmin):
class OrgAdmin(admin.ModelAdmin):

    class Meta:
		model = Organisation

    list_display = ('name','org_type')
    search_fields =	 ('name',)
    inlines = [LocationInline, InstrumentInline]


class BookingAdmin(admin.ModelAdmin):

    class Meta:
		model = Booking

    list_display = ('client','booker', 'location', 'instrument', 'provider')
    search_fields =	 ('client__name','location__name', 'instrument__name', 'provider__username', 'booker_username')
    fields = [ 'client', 'booker', 'requested_from', 'requested_to', 'duration', 'location', 'instrument', 'deadline', 'client_ref', 'comments']


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Organisation, OrgAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Booking, BookingAdmin)