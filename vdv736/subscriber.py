import uuid

from .isotime import timestamp
from .model import Subscription
from .request import SituationExchangeSubscriptionRequest


class Subscriber():

    def __init__(self):
        self._subscriptions = dict()
        self._situations = list()

    def subscribe(self, publisher_host: str, publisher_port: int, subscriber_ref: str) -> str|None:

        subscription_id = str(uuid.uuid4())
        subscription_host = publisher_host
        subscription_port = publisher_port
        subscription_termination = timestamp(60 * 60 * 24)

        subscription = Subscription(subscription_id, subscription_host, subscription_port, subscriber_ref, subscription_termination)
        self._subscriptions[subscription_id] = subscription

        request = SituationExchangeSubscriptionRequest(subscription)
        if request.execute():
            return subscription_id
        else:
            return None
        
    def unsubscribe(self, subscription_id: str) -> bool:
        
        subscriptions = self._subscriptions[subscription_id]
        
        # create termination request here ...
        result = True

        if result:
            del self._subscriptions[subscription_id]
        
        return result



