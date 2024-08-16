


class Subscription:

    def __init__(self, id: str, host: str, port: int, subscriber: str, termination: str):
        self.id = id
        self.host = host
        self.port = port
        self.subscriber = subscriber
        self.termination = termination

        self.status_endpoint = '/status'
        self.subscribe_endpoint = '/subscribe'
        self.unsubscribe_endpoint = '/unsubscribe'

        self.healthy = True

