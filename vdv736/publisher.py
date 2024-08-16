import logging
import requests
import uuid

from .model import Subscription
from .request import xml2siri_request
from .response import SubscriptionResponse
from .response import TerminateSubscriptionResponse

from fastapi import FastAPI
from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
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

        self._subscriptions = dict()
        self._situation_index = ShareableList([('0' * 36) for _ in range(5000)], name='vdv736.publisher.situation.index')

    def create_endpoint(self, subscribe_endpoint='/subscribe', unsubscribe_endpoint='/unsubscribe'):

        self._router.add_api_route(subscribe_endpoint, self._subscribe, methods=['POST'])
        self._router.add_api_route(unsubscribe_endpoint, self._unsubscribe, methods=['POST'])
        
        self._endpoint.include_router(self._router)

        return self._endpoint
    
    async def _subscribe(self, req: Request) -> None:
        request = xml2siri_request(await req.body())

        # add subscription parameters to subscription index
        subscription_id = request.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriptionIdentifier
        subscription_termination = request.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.InitialTerminationTime

        subscription = Subscription(
            subscription_id,
            None,
            None,
            request.Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriberRef,
            subscription_termination
        )
            
        try:
            self._subscriptions[subscription_id] = subscription

            # respond with SubscriptionResponse OK
            response = SubscriptionResponse('PY_TEST_PUBLISHER')
            response.ok(subscription_id, subscription_termination)

            return Response(content=response.xml(), media_type='application/xml')
        except Exception:
            # respond with SubscriptionResponse Error
            response = SubscriptionResponse('PY_TEST_PUBLISHER')
            response.error(subscription_id)

            return Response(content=response.xml(), media_type='application/xml')

    async def _unsubscribe(self, req: Request) -> None:
        request = xml2siri_request(await req.body())

        subscriber_ref = request.Siri.TerminateSubscriptionRequest.RequestorRef

        # check which subscription should be deleted - currently, only all subscriptions by a certain subscriber can be deleted
        subscriptions_to_delete = list()

        for subscription_id, subscription in self._subscriptions.items():
            if subscription.subscriber == subscriber_ref:
                subscriptions_to_delete.append(subscription_id)

        response = TerminateSubscriptionResponse('PY_TEST_PUBLISHER')
        for subscription_id in subscriptions_to_delete:
            try:
                # delete subscription from subscription stack
                del self._subscriptions[subscription_id]

                # respond with SubscriptionResponse OK
                response.add_ok(subscriber_ref, subscription_id)
                
            except Exception:
                # respond with SubscriptionResponse Error for this subscription
                response.add_error(subscriber_ref, subscription_id)

        return Response(content=response.xml(), media_type='application/xml')

    async def _rss(self) -> None:
        pass