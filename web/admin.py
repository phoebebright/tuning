from django import forms
from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import ugettext, ugettext_lazy as _

from django.forms.widgets import TextInput

from django_google_maps.widgets import GoogleMapsAddressWidget
from django_google_maps.fields import AddressField, GeoLocationField


#import reversion

from web.models import *
#TODO: user admin is not working, can't get to second screen


class CustomUserCreationForm(UserCreationForm):
    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            self._meta.model._default_manager.get(username=username)
        except self._meta.model.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])

    class Meta:
        model = CustomUser
        fields = ("username",)


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'mobile','is_active', 'date_joined', 'last_login', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'last_login')
    search_fields =	  ('email', 'first_name', 'last_name', 'username')
    list_display_links = ('email', 'username')
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

class BookerUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name','client', 'mobile','is_active', 'date_joined', 'last_login', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'mobile')}),
        (_('Preferences'), {'fields': ('is_active', 'client')}),
    )
    add_form = CustomUserCreationForm

class TunerUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name','provider', 'mobile','is_active', 'date_joined', 'last_login', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'mobile')}),
        (_('Preferences'), {'fields': ('is_active', 'activities', 'use_email','use_sms')}),
    )
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

class StudioAdmin(admin.ModelAdmin):

    ordering = ('name', )
    formfield_overrides = {
        AddressField: {'widget': GoogleMapsAddressWidget},
        GeoLocationField: {'widget': TextInput(attrs={'readonly': 'readonly'})},
                    }


class BookerInline(admin.TabularInline):
    model           = Booker
    fields = ['username','email','password']

class StudioInline(admin.TabularInline):
    model           = Studio
    fields = ['name', ]


class InstrumentInline(admin.TabularInline):
    model           = Instrument


class ActivityAdmin(admin.ModelAdmin):

    class Meta:
        model = Activity

    list_display = ('name', 'name_plural')



#class OrgAdmin(reversion.VersionAdmin):
class ClientAdmin(admin.ModelAdmin):

    class Meta:
		model = Client

    list_display = ('name',)
    search_fields =	 ('name',)
    inlines = [BookerInline, StudioInline, InstrumentInline]
    ordering = ('name', )


class ProviderAdmin(admin.ModelAdmin):

    class Meta:
		model = Provider

    list_display = ('name',)
    search_fields =	 ('name',)


class BookingAdmin(admin.ModelAdmin):

    class Meta:
		model = Booking

    list_display = ('status','client','booker', 'deadline', 'studio', 'instrument', 'tuner')
    search_fields =	 ('client__name','studio__name', 'instrument__name', 'tuner__username', 'booker_username')
    fields = [ 'client', 'booker','tuner', 'requested_from', 'requested_to', 'duration', 'studio', 'instrument', 'deadline', 'client_ref']
    list_filter = ('status','client','booker', 'deadline', 'studio', 'instrument', 'tuner')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Booker, BookerUserAdmin)
admin.site.register(Tuner, TunerUserAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Provider, ProviderAdmin)
admin.site.register(Studio, StudioAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Activity, ActivityAdmin)