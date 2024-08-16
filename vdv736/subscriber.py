import logging
import requests
import uuid
import uvicorn

from .isotime import timestamp
from .model import Subscription
from .request import SiriRequest
from .request import CheckStatusRequest
from .request import SituationExchangeSubscriptionRequest
from .request import TerminateSubscriptionRequest
from .response import xml2siri_response
from .response import SiriResponse

from fastapi import FastAPI
from fastapi import APIRouter
from threading import Thread


class Subscriber():

    def __init__(self):
        self._logger = logging.getLogger('uvicorn')

        self._subscriptions = dict()

    def __enter__(self):
        self._endpoint_thread = Thread(target=self._run_endpoint, args=(), daemon=True)
        self._endpoint_thread.start()

        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if self._endpoint_thread is not None:
            self._endpoint_thread.join(5)

    def status(self, subscription_id=None) -> bool:
        if subscription_id is not None:
            subscription = self._subscriptions[subscription_id]

            request = CheckStatusRequest(subscription)
            response = self._send_request(subscription, request)

            if response is not None and response.Siri.CheckStatusResponse.Status == True:
                self._logger.info(f"Status for subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} OK")
                return True
            else:
                self._logger.error(f"Status for subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} OK")
                
                subscription.healthy = False
                return False
        else:
            all_subscriptions_ok = True
            for subscription_id, subscription in self._subscriptions.items():
                request = CheckStatusRequest(subscription)
                response = self._send_request(subscription, request)

                if response is not None and response.Siri.CheckStatusResponse.Status == True:
                    self._logger.info(f"Status for subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} OK")
                else:
                    self._logger.error(f"Status for subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} OK")
                    
                    subscription.healthy = False
                    all_subscriptions_ok = False

            return all_subscriptions_ok

    def subscribe(self, publisher_host: str, publisher_port: int, subscriber_ref: str, status_endpoint='/status', subscribe_endpoint='/subscribe', unsubscribe_endpoint='/unsubscribe') -> str|None:

        subscription_id = str(uuid.uuid4())
        subscription_host = publisher_host
        subscription_port = publisher_port
        subscription_termination = timestamp(60 * 60 * 24)

        subscription = Subscription(subscription_id, subscription_host, subscription_port, subscriber_ref, subscription_termination)
        subscription.status_endpoint = status_endpoint
        subscription.subscribe_endpoint = subscribe_endpoint
        subscription.unsubscribe_endpoint = unsubscribe_endpoint

        self._subscriptions[subscription_id] = subscription

        request = SituationExchangeSubscriptionRequest(subscription)
        response = self._send_request(subscription, request)

        if response.Siri.SubscriptionResponse.ResponseStatus.Status == True:
            self._logger.info(f"Initialized subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} successfully")

            return subscription_id
        else:
            self._logger.error(f"Failed to initalize subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber}")

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
                self._logger.info(f"Terminated subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} successfully")
                
                del self._subscriptions[subscription_id]

                return True
            else:
                self._logger.error(f"Failed to terminate subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber}")

                return False
    
    def get_situations(self) -> None:
        pass
        #print(list(self._situation_index))
        #return self._situations

    def _run_endpoint(self):
        endpoint = SubscriberEndpoint().create_endpoint()

        # disable uvicorn logs
        logging.getLogger('uvicorn.error').handlers = []
        logging.getLogger('uvicorn.error').propagate = False

        logging.getLogger('uvicorn.access').handlers = []
        logging.getLogger('uvicorn.access').propagate = False

        logging.getLogger('uvicorn.asgi').handlers = []
        logging.getLogger('uvicorn.asgi').propagate = False

        # run ASGI server with endpoint
        uvicorn.run(app=endpoint, host='127.0.0.1', port=9090)

    def _send_request(self, subscription: Subscription, siri_request: SiriRequest) -> SiriResponse|None:
        try:
            if isinstance(siri_request, CheckStatusRequest):
                endpoint = f"{subscription.host}:{subscription.port}/{subscription.status_endpoint}"
            elif isinstance(siri_request, SituationExchangeSubscriptionRequest):
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
            self._logger.exception(exception)

            return None


class SubscriberEndpoint():

    def __init__(self):
        self._router = APIRouter()
        self._endpoint = FastAPI()

    def create_endpoint(self, subscription_endpoint='/subscription/{subscription_id}'):

        self._router.add_api_route(subscription_endpoint, self._subscription, methods=['POST'])
        
        self._endpoint.include_router(self._router)

        return self._endpoint
    
    async def _subscription(self, subscription_id: str) -> None:
        pass
        # this is how to add a situation ID to the situation index
        """for index, situation_id in enumerate(list(self._situation_index)):
            print(situation_id)
            if not situation_id.startswith('00000000'):
                continue

            self._situation_index[index] = subscription_id
            break"""
        
