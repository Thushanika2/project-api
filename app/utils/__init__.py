from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def overlaps(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1
