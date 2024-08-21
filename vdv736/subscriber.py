import logging
import requests
import uuid
import uvicorn
import yaml

from .isotime import timestamp
from .database import local_node_database
from .delivery import xml2siri_delivery
from .delivery import SituationExchangeDelivery
from .model import PublicTransportSituation
from .model import Subscription
from .request import SiriRequest
from .request import CheckStatusRequest
from .request import SituationExchangeSubscriptionRequest
from .request import TerminateSubscriptionRequest
from .request import SituationExchangeRequest
from .response import xml2siri_response
from .response import SiriResponse
from .response import DataReceivedAcknowledgement
from .sirixml import exists as sirixml_exists
from .sirixml import get_elements as sirixml_get_elements
from .sirixml import get_value as sirixml_get_value

from fastapi import FastAPI
from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
from threading import Thread


class Subscriber():

    def __init__(self, participant_ref: str, participant_config_filename: str):
        self._service_participant_ref = participant_ref
        self._logger = logging.getLogger('uvicorn')

        self._local_node_database = local_node_database('vdv736.subscriber')

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

    def get_situations(self) -> dict[str, PublicTransportSituation]:
        return self._local_node_database.get_situations()

    def status(self, subscription_id=None) -> bool:
        if subscription_id is not None:
            return self._status(subscription_id)
        else:
            all_subscriptions_ok = True
            for subscription_id, _ in self._local_node_database.get_subscriptions().items():
                if self._status(subscription_id) != True:
                    all_subscriptions_ok = False

            return all_subscriptions_ok
        
    def _status(self, subscription_id: str) -> bool:
        subscription = self._local_node_database.get_subscriptions()[subscription_id]

        request = CheckStatusRequest(subscription)
        response = self._send_request(subscription, request)

        if sirixml_get_value(response, 'Siri.CheckStatusResponse.Status', False):
            if subscription.remote_service_startup_time is not None:
                if sirixml_get_value(response, 'Siri.CheckStatusResponse.ServiceStartedTime') == subscription.remote_service_startup_time:
                    self._logger.info(f"Status for subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} OK")
                    return True
                else:
                    self._logger.warn(f"Remote server for subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} seems to be restarted")
                    
                    self.unsubscribe(subscription.id)
                    return self.subscribe(subscription.remote_service_participant_ref) is not None
            else:
                subscription.remote_service_startup_time = sirixml_get_value(response, 'Siri.CheckStatusResponse.ServiceStartedTime')
                self._local_node_database.update_subscription(subscription_id, subscription)

                self._logger.info(f"Status for subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} OK")
                return True
        else:
            self._logger.error(f"Status for subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} FAIL")
            return False

    def subscribe(self, participant_ref: str) -> str|None:

        subscription_id = str(uuid.uuid4())
        subscription_host = self._participant_config[participant_ref]['host']
        subscription_port = self._participant_config[participant_ref]['port']
        subscription_protocol = self._participant_config[participant_ref]['protocol']
        subscription_termination = timestamp(60 * 60 * 24)

        subscription = Subscription.create(subscription_id, subscription_host, subscription_port, subscription_protocol, self._service_participant_ref, subscription_termination)
        subscription.status_endpoint = self._participant_config[participant_ref]['status_endpoint']
        subscription.subscribe_endpoint = self._participant_config[participant_ref]['subscribe_endpoint']
        subscription.unsubscribe_endpoint = self._participant_config[participant_ref]['unsubscribe_endpoint']

        subscription.remote_service_participant_ref = participant_ref

        request = SituationExchangeSubscriptionRequest(subscription)
        response = self._send_request(subscription, request)

        if sirixml_get_value(response, 'Siri.SubscriptionResponse.ResponseStatus.Status', True):
            self._logger.info(f"Initialized subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} successfully")

            service_started_time = sirixml_get_value(response, 'Siri.SubscriptionResponse.ResponseStatus.ServiceStartedTime')
            if service_started_time is not None:
                subscription.remote_service_startup_time = service_started_time
                
            self._local_node_database.add_subscription(subscription_id, subscription)

            return subscription_id
        else:
            self._logger.error(f"Failed to initalize subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber}")

            return None
        
    def unsubscribe(self, subscription_id: str) -> bool:
        
        # take subscription instance from subscription stack
        subscription = self._local_node_database.get_subscriptions()[subscription_id]

        # delete subscription out of local database
        self._local_node_database.remove_subscription(subscription_id)
        
        # create termination request here ...
        request = TerminateSubscriptionRequest(self._service_participant_ref)
        response = self._send_request(subscription, request)

        # check each termination subscription response for success
        if sirixml_exists(response, 'Siri.TerminationSubscriptionResponse.TerminationResponseStatus'):
            for termination_response_status in sirixml_get_elements(response, 'Siri.TerminationSubscriptionResponse.TerminationResponseStatus'):
                if termination_response_status.Status == True:
                    self._logger.info(f"Terminated subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} successfully")
                    return True
                else:
                    self._logger.error(f"Failed to terminate subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber}")
                    return False
        else:
            # publisher returns no termination status at all, that means, there were no subscriptions at publisher side ... good anyway
            self._logger.info(f"Terminated subscription {subscription.id} @ {subscription.host}:{subscription.port} as {subscription.subscriber} successfully")
            return True
            
    def request(self, publisher_ref: str) -> bool:

        # generate SituationExchangeRequest
        request = SituationExchangeRequest(self._service_participant_ref)
        delivery = self._send_direct_request(publisher_ref, request)

        if delivery is not None:
            # process service delivery ...
            for pts in sirixml_get_elements(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.Situations.PtSituationElement'):
                situation_id = sirixml_get_value(pts, 'SituationNumber')
                self._local_node_database.add_situation(situation_id, pts)

            return True
        else:
            self._logger.error(f"Failed to request data from {publisher_ref}")

            return False


    def _run_endpoint(self) -> None:
        self._endpoint = SubscriberEndpoint(self._service_participant_ref)

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

    def _send_request(self, subscription: Subscription, siri_request: SiriRequest) -> SiriResponse|None:
        try:
            if isinstance(siri_request, CheckStatusRequest):
                endpoint = f"{subscription.protocol}://{subscription.host}:{subscription.port}/{subscription.status_endpoint}"
            elif isinstance(siri_request, SituationExchangeSubscriptionRequest):
                endpoint = f"{subscription.protocol}://{subscription.host}:{subscription.port}/{subscription.subscribe_endpoint}"
            elif isinstance(siri_request, TerminateSubscriptionRequest):
                endpoint = f"{subscription.protocol}://{subscription.host}:{subscription.port}/{subscription.unsubscribe_endpoint}"
            
            headers = {
                "Content-Type": "application/xml"
            }
            
            response_xml = requests.post(endpoint, headers=headers, data=siri_request.xml())
            response = xml2siri_response(response_xml.content)

            return response
        except Exception as ex:
            self._logger.error(ex)
            return None
        
    def _send_direct_request(self, publisher_ref: str, siri_request: SiriRequest) -> SituationExchangeDelivery|None:
        try:
            subscription_host = self._participant_config[publisher_ref]['host']
            subscription_port = self._participant_config[publisher_ref]['port']
            subscription_protocol = self._participant_config[publisher_ref]['protocol']
            
            if isinstance(siri_request, SituationExchangeRequest):
                request_endpoint = self._participant_config[publisher_ref]['request_endpoint']
                endpoint = f"{subscription_protocol}://{subscription_host}:{subscription_port}/{request_endpoint}"
            
            headers = {
                "Content-Type": "application/xml"
            }
            
            response_xml = requests.post(endpoint, headers=headers, data=siri_request.xml())
            delivery = xml2siri_delivery(response_xml.content)

            return delivery
        except Exception as ex:
            self._logger.error(ex)
            return None


class SubscriberEndpoint():

    def __init__(self, participant_ref: str):
        self._service_participant_ref = participant_ref
        self._service_startup_time = timestamp()
        self._logger = logging.getLogger('uvicorn')

        self._router = APIRouter()
        self._endpoint = FastAPI()

        self._local_node_database = local_node_database('vdv736.subscriber')

    def create_endpoint(self, participant_ref: str, delivery_endpoint='/delivery') -> FastAPI:
        self.participant_ref = participant_ref

        self._router.add_api_route(delivery_endpoint, self._delivery, methods=['POST'])
        
        self._endpoint.include_router(self._router)

        return self._endpoint
    
    def terminate(self) -> None:
        self._local_node_database.close()
    
    async def _delivery(self, req: Request) -> Response:
        try:
            delivery = xml2siri_delivery(await req.body())

            # process service delivery ...
            for pts in sirixml_get_elements(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.Situations.PtSituationElement'):
                situation_id = sirixml_get_value(pts, 'SituationNumber')
                self._local_node_database.add_situation(situation_id, pts)

            # create data acknowledgement with OK status
            acknowledgement = DataReceivedAcknowledgement(
                sirixml_get_value(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.SubscriberRef'), 
                sirixml_get_value(delivery, 'Siri.ServiceDelivery.ResponseMessageIdentifier')
            )

            acknowledgement.ok()

            return Response(content=acknowledgement.xml(), media_type='application/xml')
        except Exception as ex:
            self._logger.error(ex)

            # create data acknowledgement
            acknowledgement = DataReceivedAcknowledgement(
                sirixml_get_value(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.SubscriberRef'), 
                sirixml_get_value(delivery, 'Siri.ServiceDelivery.ResponseMessageIdentifier')
            )

            acknowledgement.error()

            return Response(content=acknowledgement.xml(), media_type='application/xml')
        
