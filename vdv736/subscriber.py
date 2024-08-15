import logging
import uuid

from .isotime import timestamp
from .model import Subscription
from .request import SituationExchangeSubscriptionRequest

from fastapi import FastAPI
from fastapi import APIRouter
from multiprocessing.shared_memory import ShareableList


class SubscriberController():

    def __init__(self):
        self._subscriptions = dict()

        self._situation_index = ShareableList(name='vdv736.subscriber.situation.index')

    def subscribe(self, publisher_host: str, publisher_port: int, subscriber_ref: str, subscribe_endpoint='/subscribe', unsubscribe_endpoint='/unsubscribe') -> str|None:

        subscription_id = str(uuid.uuid4())
        subscription_host = publisher_host
        subscription_port = publisher_port
        subscription_termination = timestamp(60 * 60 * 24)

        subscription = Subscription(subscription_id, subscription_host, subscription_port, subscriber_ref, subscription_termination)
        subscription.subscribe_endpoint = subscribe_endpoint
        subscription.unsubscribe_endpoint = unsubscribe_endpoint

        self._subscriptions[subscription_id] = subscription

        request = SituationExchangeSubscriptionRequest(subscription)
        if request.execute():
            logging.info(f"Initialized subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} successfully")

            return subscription_id
        else:
            logging.error(f"Failed to initalize subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber}")

            return None
        
    def unsubscribe(self, subscription_id: str) -> bool:
        
        if subscription_id not in self._subscriptions.keys():
            return

        subscription = self._subscriptions[subscription_id]
        
        # create termination request here ...
        result = True

        if result:
            del self._subscriptions[subscription_id]

        return result
    
    def get_situations(self) -> None:
        pass
        #print(list(self._situation_index))
        #return self._situations


class SubscriberEndpoint():

    def __init__(self):
        self._router = APIRouter()
        self._endpoint = FastAPI()

        self._router.add_api_route('/rss', self._rss, methods=['GET'])

        self._situation_index = ShareableList([('0' * 36) for _ in range(5000)], name='vdv736.subscriber.situation.index')

    def create_endpoint(self, subscription_endpoint='/subscription/{subscription_id}'):

        self._router.add_api_route(subscription_endpoint, self._subscription, methods=['POST'])
        
        self._endpoint.include_router(self._router)

        return self._endpoint
    
    async def _subscription(self, subscription_id: str) -> None:

        # this is how to add a situation ID to the situation index
        for index, situation_id in enumerate(list(self._situation_index)):
            print(situation_id)
            if not situation_id.startswith('00000000'):
                continue

            self._situation_index[index] = subscription_id
            break

    async def _rss(self) -> None:
        pass