import logging
import requests
import uuid

from .isotime import timestamp
from .model import Subscription
from .request import SiriRequest
from .request import SituationExchangeSubscriptionRequest
from .request import TerminateSubscriptionRequest
from .response import xml2siri_response
from .response import SiriResponse

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
        response = self._send_request(subscription, request)

        if response.Siri.SubscriptionResponse.ResponseStatus.Status == True:
            logging.info(f"Initialized subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} successfully")

            return subscription_id
        else:
            logging.error(f"Failed to initalize subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber}")

            return None
        
    def unsubscribe(self, subscription_id: str) -> bool:
        
        # take subscription instance from subscription stack
        subscription = self._subscriptions[subscription_id]
        
        # create termination request here ...
        request = TerminateSubscriptionRequest(subscription)
        response = self._send_request(subscription, request)

        # check each termination subscription response for success
        for termination_response_status in response.Siri.TerminationSubscriptionResponse.TerminationResponseStatus:
            if termination_response_status.Status == True:
                logging.info(f"Terminated subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} successfully")
                
                del self._subscriptions[subscription_id]

                return True
            else:
                logging.error(f"Failed to terminate subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber}")

                return False
    
    def get_situations(self) -> None:
        pass
        #print(list(self._situation_index))
        #return self._situations

    def _send_request(self, subscription: Subscription, siri_request: SiriRequest) -> SiriResponse:
        try:
            if isinstance(siri_request, SituationExchangeSubscriptionRequest):
                endpoint = f"{subscription.host}:{subscription.port}/{subscription.subscribe_endpoint}"
            elif isinstance(siri_request, TerminateSubscriptionRequest):
                endpoint = f"{subscription.host}:{subscription.port}/{subscription.unsubscribe_endpoint}"
            
            headers = {
                "Content-Type": "application/xml"
            }
            
            response_xml = requests.post(endpoint, headers=headers, data=siri_request.xml())
            response = xml2siri_response(response_xml.content)

            return response
        except Exception as exception:
            logging.exception(exception)


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