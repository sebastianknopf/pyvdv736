import logging
import requests
import uuid
import uvicorn

from .isotime import timestamp
from .model import Subscription
from .request import xml2siri_request
from .response import CheckStatusResponse
from .response import SubscriptionResponse
from .response import TerminateSubscriptionResponse

from fastapi import FastAPI
from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
from threading import Thread


class Publisher():

    def __init__(self, participant_ref: str):
        self._service_participant_ref = participant_ref
        self._logger = logging.getLogger('uvicorn')

        self._subscriptions = dict()

    def __enter__(self):
        self._endpoint_thread = Thread(target=self._run_endpoint, args=(), daemon=True)
        self._endpoint_thread.start()

        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if self._endpoint_thread is not None:
            self._endpoint_thread.join(5)    
    
    def publish(self) -> None:
        pass

    def _run_endpoint(self):
        endpoint = PublisherEndpoint().create_endpoint(self._service_participant_ref)

        # disable uvicorn logs
        logging.getLogger('uvicorn.error').handlers = []
        logging.getLogger('uvicorn.error').propagate = False

        logging.getLogger('uvicorn.access').handlers = []
        logging.getLogger('uvicorn.access').propagate = False

        logging.getLogger('uvicorn.asgi').handlers = []
        logging.getLogger('uvicorn.asgi').propagate = False

        # run ASGI server with endpoint
        uvicorn.run(app=endpoint, host='127.0.0.1', port=9091)


class PublisherEndpoint():

    def __init__(self):
        self._service_started_time = timestamp()
        self._logger = logging.getLogger('uvicorn')

        self._router = APIRouter()
        self._endpoint = FastAPI()

        self._subscriptions = dict()

    def create_endpoint(self, participant_ref: str, status_endpoint='/status', subscribe_endpoint='/subscribe', unsubscribe_endpoint='/unsubscribe'):
        self._participant_ref = participant_ref

        self._router.add_api_route(status_endpoint, self._status, methods=['POST'])
        self._router.add_api_route(subscribe_endpoint, self._subscribe, methods=['POST'])
        self._router.add_api_route(unsubscribe_endpoint, self._unsubscribe, methods=['POST'])
        
        self._endpoint.include_router(self._router)

        return self._endpoint
    
    async def _status(self, req: Request) -> Response:
        request = xml2siri_request(await req.body())

        # simply respond with current status
        response = CheckStatusResponse(self._service_started_time)
        return Response(content=response.xml(), media_type='application/xml')

    async def _subscribe(self, req: Request) -> Response:
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
            response = SubscriptionResponse(self._participant_ref)
            response.ok(subscription_id, subscription_termination)

            return Response(content=response.xml(), media_type='application/xml')
        except Exception:
            # respond with SubscriptionResponse Error
            response = SubscriptionResponse(self._participant_ref)
            response.error(subscription_id)

            return Response(content=response.xml(), media_type='application/xml')

    async def _unsubscribe(self, req: Request) -> Response:
        request = xml2siri_request(await req.body())

        subscriber_ref = request.Siri.TerminateSubscriptionRequest.RequestorRef

        # check which subscription should be deleted - currently, only all subscriptions by a certain subscriber can be deleted
        subscriptions_to_delete = list()

        for subscription_id, subscription in self._subscriptions.items():
            if subscription.subscriber == subscriber_ref:
                subscriptions_to_delete.append(subscription_id)

        response = TerminateSubscriptionResponse(self._participant_ref)
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

