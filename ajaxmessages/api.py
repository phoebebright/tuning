from ajaxmessages.models import Message

PENDING = 'p'
SUCCESS = 's'
FAILURE = 'f'


def add_message(user, text, status=SUCCESS):
    return Message.objects.create(user=user, text=text, status=status)


