import logging
import uuid

from .isotime import timestamp
from .model import Subscription
from .request import SituationExchangeSubscriptionRequest

from fastapi import FastAPI
from fastapi import APIRouter
from multiprocessing.shared_memory import ShareableList


class PublisherController():

    def __init__(self):
        self._subscriptions = dict()

        self._situation_index = ShareableList(name='vdv736.publisher.situation.index')
    
    def publish(self) -> None:
        pass


class PublisherEndpoint():

    def __init__(self):
        self._router = APIRouter()
        self._endpoint = FastAPI()

        self._router.add_api_route('/rss', self._rss, methods=['GET'])

        self._subscription_index = ShareableList([('0' * 36) for _ in range(100)], name='vdv736.publisher.subscription.index')
        self._situation_index = ShareableList([('0' * 36) for _ in range(5000)], name='vdv736.publisher.situation.index')

    def create_endpoint(self, subscribe_endpoint='/subscribe', unsubscribe_endpoint='/unsubscribe'):

        self._router.add_api_route(subscribe_endpoint, self._subscribe, methods=['POST'])
        self._router.add_api_route(unsubscribe_endpoint, self._unsubscribe, methods=['POST'])
        
        self._endpoint.include_router(self._router)

        return self._endpoint
    
    async def _subscribe(self) -> None:

        # this is how to add a situation ID to the situation index
        for index, situation_id in enumerate(list(self._situation_index)):
            print(situation_id)
            if not situation_id.startswith('00000000'):
                continue

            self._situation_index[index] = None
            break

    async def _unsubscribe(self) -> None:
        pass

    async def _rss(self) -> None:
        pass