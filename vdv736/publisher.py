import logging
import requests
import time
import uvicorn
import yaml

from .isotime import timestamp
from .database import local_node_database
from .delivery import ServiceDelivery
from .delivery import SituationExchangeDelivery
from .model import PublicTransportSituation
from .model import Subscription
from .request import xml2siri_request
from .response import xml2siri_response
from .response import SiriResponse
from .response import CheckStatusResponse
from .response import SubscriptionResponse
from .response import TerminateSubscriptionResponse
from .sirixml import get_elements as sirixml_get_elements
from .sirixml import get_value as sirixml_get_value

from fastapi import FastAPI
from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
from threading import Thread


class Publisher():

    def __init__(self, participant_ref: str, participant_config_filename: str):
        self._service_participant_ref = participant_ref
        self._logger = logging.getLogger('uvicorn')

        self._local_node_database = local_node_database('vdv736.publisher')

        try:
            with open(participant_config_filename) as participant_config_file:
                self._participant_config = yaml.safe_load(participant_config_file)
        except Exception as ex:
            self._logger.error(ex)

    def __enter__(self):
        self._endpoint_thread = Thread(target=self._run_endpoint, args=(), daemon=True)
        self._endpoint_thread.start()

        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        if self._endpoint is not None:
            self._endpoint.terminate()
        
        if self._endpoint_thread is not None:
            self._endpoint_thread.join(1)

        if self._local_node_database is not None:
            self._local_node_database.close(True)
    
    def publish_situation(self, situation: PublicTransportSituation) -> None:
        situation_id = sirixml_get_value(situation, 'SituationNumber')
        self._local_node_database.add_situation(situation_id, situation)
        
        for _, subscription in self._local_node_database.get_subscriptions().items():
            delivery = SituationExchangeDelivery(self._service_participant_ref, subscription)
            delivery.add_situation(situation)

            response = self._send_delivery(subscription, delivery)

            if sirixml_get_value(response, 'Siri.DataReceivedAcknowledgement.Status', False):
                self._logger.info(f"Sent delivery for subscription {subscription.id} to {subscription.subscriber} successfully")
            else:
                self._logger.error(f"Failed to send delivery for subscription {subscription.id} to {subscription.subscriber}")

    def _run_endpoint(self) -> None:
        self._endpoint = PublisherEndpoint(self._service_participant_ref)

        # disable uvicorn logs
        logging.getLogger('uvicorn.error').handlers = []
        logging.getLogger('uvicorn.error').propagate = False

        logging.getLogger('uvicorn.access').handlers = []
        logging.getLogger('uvicorn.access').propagate = False

        logging.getLogger('uvicorn.asgi').handlers = []
        logging.getLogger('uvicorn.asgi').propagate = False

        # run ASGI server with endpoint
        endpoint_host = self._participant_config[self._service_participant_ref]['host']
        endpoint_port = self._participant_config[self._service_participant_ref]['port']

        uvicorn.run(app=self._endpoint.create_endpoint(self._service_participant_ref), host=endpoint_host, port=endpoint_port)        

    def _send_delivery(self, subscription: Subscription, siri_delivery: ServiceDelivery) -> SiriResponse|None:
        try:
            subscription_host = self._participant_config[subscription.subscriber]['host']
            subscription_port = self._participant_config[subscription.subscriber]['port']
            subscription_protocol = self._participant_config[subscription.subscriber]['protocol']
            
            if isinstance(siri_delivery, SituationExchangeDelivery):
                delivery_endpoint = self._participant_config[subscription.subscriber]['delivery_endpoint']
                endpoint = f"{subscription_protocol}://{subscription_host}:{subscription_port}/{delivery_endpoint}"

            headers = {
                "Content-Type": "application/xml"
            }
            
            response_xml = requests.post(endpoint, headers=headers, data=siri_delivery.xml())
            response = xml2siri_response(response_xml.content)

            return response
        except Exception as exception:
            self._logger.exception(exception)

            return None


class PublisherEndpoint():

    def __init__(self, participant_ref: str):
        self._service_participant_ref = participant_ref
        self._service_startup_time = timestamp()
        self._logger = logging.getLogger('uvicorn')

        self._router = APIRouter()
        self._endpoint = FastAPI()

        self._local_node_database = local_node_database('vdv736.publisher')

    def create_endpoint(self, participant_ref: str, status_endpoint='/status', subscribe_endpoint='/subscribe', unsubscribe_endpoint='/unsubscribe', request_endpoint='/request') -> FastAPI:
        self._participant_ref = participant_ref

        self._router.add_api_route(status_endpoint, self._status, methods=['POST'])
        self._router.add_api_route(subscribe_endpoint, self._subscribe, methods=['POST'])
        self._router.add_api_route(unsubscribe_endpoint, self._unsubscribe, methods=['POST'])
        self._router.add_api_route(request_endpoint, self._request, methods=['POST'])
        
        self._endpoint.include_router(self._router)

        return self._endpoint
    
    def terminate(self):
        self._local_node_database.close()
    
    async def _status(self, req: Request) -> Response:
        request = xml2siri_request(await req.body())

        # simply respond with current status
        response = CheckStatusResponse(self._service_startup_time)
        return Response(content=response.xml(), media_type='application/xml')

    async def _subscribe(self, req: Request) -> Response:
        request = xml2siri_request(await req.body())

        # add subscription parameters to subscription index
        subscription_id = sirixml_get_value(request, 'Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriptionIdentifier')
        subscription_termination = sirixml_get_value(request, 'Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.InitialTerminationTime')

        subscription = Subscription.create(
            subscription_id,
            None,
            None,
            None,
            sirixml_get_value(request, 'Siri.SubscriptionRequest.SituationExchangeSubscriptionRequest.SubscriberRef'),
            subscription_termination
        )
            
        try:
            result = self._local_node_database.add_subscription(subscription_id, subscription)

            # respond with SubscriptionResponse OK
            response = SubscriptionResponse(self._participant_ref, self._service_startup_time)

            if result == True:
                response.ok(subscription_id, subscription_termination)
            else:
                response.error(subscription_id)

            return Response(content=response.xml(), media_type='application/xml')
        except Exception as ex:
            # log exception
            self._logger.error(ex)

            # respond with SubscriptionResponse Error
            response = SubscriptionResponse(self._participant_ref, self._service_startup_time)
            response.error(subscription_id)

            return Response(content=response.xml(), media_type='application/xml')

    async def _unsubscribe(self, req: Request) -> Response:
        request = xml2siri_request(await req.body())

        subscriber_ref = sirixml_get_value(request, 'Siri.TerminateSubscriptionRequest.RequestorRef')

        # check which subscription should be deleted - currently, only all subscriptions by a certain subscriber can be deleted
        subscriptions_to_delete = list()

        for subscription_id, subscription in self._local_node_database.get_subscriptions().items():
            if subscription.subscriber == subscriber_ref:
                subscriptions_to_delete.append(subscription_id)

        response = TerminateSubscriptionResponse(self._participant_ref)
        for subscription_id in subscriptions_to_delete:
            try:
                # delete subscription from subscription stack
                result = self._local_node_database.remove_subscription(subscription_id)

                # respond with SubscriptionResponse OK or ERROR depending on result
                if result == True:
                    response.add_ok(subscriber_ref, subscription_id)
                else:
                    response.add_error(subscription_id)
                
            except Exception:
                # respond with SubscriptionResponse Error for this subscription
                response.add_error(subscriber_ref, subscription_id)

        return Response(content=response.xml(), media_type='application/xml')

    async def _request(self, req: Request) -> Response:
        request = xml2siri_request(await req.body())

        delivery = SituationExchangeDelivery(self._service_participant_ref, None)

        for _, situation in self._local_node_database.get_situations().items():
            delivery.add_situation(situation)

        return Response(content=delivery.xml(), media_type='application/xml')    

        



