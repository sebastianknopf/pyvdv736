import datetime

def timestamp(additional_seconds=0) -> str:
    ts = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)

    if additional_seconds > 0:
        ts = ts + datetime.timedelta(seconds=additional_seconds)
    
    return ts.isoformat()

