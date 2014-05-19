from django.core.exceptions import *

class ModelException(Exception):
    errorCode = 100
    txtMessage = ""
    def __init__(self, message=None, *args, **kwargs):
        if message:
            self.txtMessage = message
        print self.txtMessage

class GeneralException(ModelException):
    '''
    raised if no match found criteria when searching the pool
    '''
    txtMessage = 'General Error'
    errorCode = 101

class PastDateException(ModelException):
    '''
    raised if a date in the past is invalid
    '''
    txtMessage = 'Date/Time must be in the future'
    errorCode = 102

class DeadlineBeforeBookingException(ModelException):
    '''
    raised if a date in the past is invalid
    '''
    txtMessage = 'Deadline is before time of requested booking'
    errorCode = 103

class InvalidQueryset(ModelException):
    '''
    eg. "mine" queryset is required by user of type system as only valid for clients and providers
    '''
    txtMessage = 'Filter requested for this queryset is not valid'
    errorCode = 104

class InvalidActivity(PermissionDenied):
    '''
    eg. "mine" queryset is required by user of type system as only valid for clients and providers
    '''
    txtMessage = 'This is not a valid activity for this user'
    errorCode = 105

    def __init__(self, message=None, *args, **kwargs):
        if message:
            self.txtMessage = message
        print self.txtMessage

class InvalidID(ModelException):
    '''
    eg. incorrect client id passed to new booking
    '''
    txtMessage = 'This is not a valid id'
    errorCode = 106

class InvalidData(ModelException):
    '''
    eg. incorrect client id passed to new booking
    '''
    txtMessage = 'This is not a valid data'
    errorCode = 107

class NoSystemUser(ModelException):
    '''
    Couldnt find a user "system" in the user table
    '''
    txtMessage = 'Need to create a SYSTEM user'
    errorCode = 108

class RequestTunerFailed(ModelException):
    '''
    For a number of reasons the system has not been able to find a tuner for a booking
    '''
    txtMessage = 'Failed to request tuner - will have to request manually'
    errorCode = 109


class InvalidBookingForCall(ModelException):
    '''
    Couldnt find a user "system" in the user table
    '''
    txtMessage = 'Expecting booking to have Requested status but it does not '
    errorCode = 110







class GettingMailError(ModelException):
    '''
    Couldnt find a user "system" in the user table
    '''
    txtMessage = 'Error getting data from mailbox '
    errorCode = 201
