from datetime import datetime, date, time

def is_list(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


def make_time(dt, round_direction="start"):
    ''' convert a date to a datetime if not already a datetime
    second arguments tells whether time should be start or end of day

    '''
    if hasattr(dt, 'hour'):

        return dt

    else:
        if round_direction == "start":
            return datetime.combine(dt, time.min)
        else:
            return datetime.combine(dt, time.max)
