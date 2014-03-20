
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
