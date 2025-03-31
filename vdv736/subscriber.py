import logging
import requests
import uuid
import time
import typing
import uvicorn

from .isotime import timestamp
from .database import local_node_database
from .delivery import xml2siri_delivery
from .delivery import SiriDelivery
from .delivery import SituationExchangeDelivery
from .handler import SituationProgressHandler
from .model import PublicTransportSituation
from .model import Subscription
from .participantconfig import ParticipantConfig
from .request import InvalidMethodError
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
from fastapi import BackgroundTasks
from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
from threading import Thread


class Subscriber():

    def __init__(self, participant_ref: str, participant_config_filename: str, local_ip_address: str = '0.0.0.0', publish_subscribe: bool = True):
        self._service_participant_ref = participant_ref
        self._service_local_ip_address = local_ip_address
        self._pubsub = publish_subscribe

        self._logger = logging.getLogger('uvicorn')

        self._local_node_database = local_node_database('vdv736.subscriber')
        self._endpoint = None

        self._on_delivery = None

        try:
            self._participant_config = ParticipantConfig(participant_config_filename)
        except Exception as ex:
            self._logger.error(ex)

    def __enter__(self):

        if self._pubsub:
            self._endpoint_thread = Thread(target=self._run_endpoint, args=(), daemon=True)
            self._endpoint_thread.start()

            time.sleep(0.01) # give the endpoint thread time for startup
            self._logger.info(f"Subscriber running at {self._participant_config.participants[self._service_participant_ref]['host']}:{self._participant_config.participants[self._service_participant_ref]['port']}")
            self._logger.info(f"Local node database at {self._local_node_database._filename}")

        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        
        if self._pubsub:
            # terminate all subscriptions
            for subscription_id, subscription in self._local_node_database.get_subscriptions().items():
                self.unsubscribe(subscription_id)

            # terminate endpoint and close local database
            if self._endpoint is not None:
                self._endpoint.terminate()
            
            if self._endpoint_thread is not None:
                self._endpoint_thread.join(1)

        # local node database has to be closed anyway, regardless of using pubsub mode
        if self._local_node_database is not None:
            self._local_node_database.close(True)

    def set_callbacks(self, on_delivery_callback: typing.Callable[[SiriDelivery], None]) -> None:
        self._on_delivery = on_delivery_callback

        if self._endpoint is not None:
            self._endpoint.set_callbacks(self._on_delivery)

    def get_situations(self) -> dict[str, PublicTransportSituation]:
        return self._local_node_database.get_situations()

    def status(self, subscription_id=None) -> bool:
        if not self._pubsub:
            raise RuntimeError("Status requests are only available in publish/subscribe mode!")
        
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

        if response is not None and sirixml_get_value(response, 'Siri.CheckStatusResponse.Status', False):
            if subscription.remote_service_startup_time is not None:
                if sirixml_get_value(response, 'Siri.CheckStatusResponse.ServiceStartedTime') == subscription.remote_service_startup_time:
                    self._logger.info(f"Status for subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber} OK")
                    return True
                else:
                    self._logger.warning(f"Remote server for subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber} seems to be restarted")
                    
                    self.unsubscribe(subscription.id)
                    return self.subscribe(subscription.remote_service_participant_ref) is not None
            else:
                subscription.remote_service_startup_time = sirixml_get_value(response, 'Siri.CheckStatusResponse.ServiceStartedTime')
                self._local_node_database.update_subscription(subscription_id, subscription)

                self._logger.info(f"Status for subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber} OK")
                return True
        else:
            self._logger.error(f"Status for subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber} FAIL")
            return False

    def subscribe(self, participant_ref: str) -> str|None:

        if not self._pubsub:
            raise RuntimeError("Subscriptions can only be initialized in publish/subscribe mode!")
        
        subscription_id = str(uuid.uuid4())
        subscription_host = self._participant_config.participants[participant_ref]['host']
        subscription_port = self._participant_config.participants[participant_ref]['port']
        subscription_protocol = self._participant_config.participants[participant_ref]['protocol']
        subscription_termination = timestamp(60 * 60 * 24)

        subscription = Subscription.create(subscription_id, subscription_host, subscription_port, subscription_protocol, self._service_participant_ref, subscription_termination)
        subscription.single_endpoint = self._participant_config.participants[participant_ref]['single_endpoint']
        subscription.status_endpoint = self._participant_config.participants[participant_ref]['status_endpoint']
        subscription.subscribe_endpoint = self._participant_config.participants[participant_ref]['subscribe_endpoint']
        subscription.unsubscribe_endpoint = self._participant_config.participants[participant_ref]['unsubscribe_endpoint']

        subscription.remote_service_participant_ref = participant_ref

        request = SituationExchangeSubscriptionRequest(subscription)
        response = self._send_request(subscription, request)

        if response is not None and sirixml_get_value(response, 'Siri.SubscriptionResponse.ResponseStatus.Status', True):
            self._logger.info(f"Initialized subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber} successfully")

            service_started_time = sirixml_get_value(response, 'Siri.SubscriptionResponse.ResponseStatus.ServiceStartedTime')
            if service_started_time is not None:
                subscription.remote_service_startup_time = service_started_time
                
            self._local_node_database.add_subscription(subscription_id, subscription)

            return subscription_id
        else:
            self._logger.error(f"Failed to initalize subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber}")

            return None
        
    def unsubscribe(self, subscription_id: str) -> bool:
        
        if not self._pubsub:
            raise RuntimeError("Subscriptions can only be terminated in publish/subscribe mode!")
        
        # take subscription instance from subscription stack
        subscription = self._local_node_database.get_subscriptions()[subscription_id]

        # delete subscription out of local database
        self._local_node_database.remove_subscription(subscription_id)
        
        # create termination request here ...
        request = TerminateSubscriptionRequest(self._service_participant_ref)
        request.subscription(self._service_participant_ref, subscription_id)

        response = self._send_request(subscription, request)

        # check each termination subscription response for success
        if response is not None:
            if sirixml_exists(response, 'Siri.TerminationSubscriptionResponse.TerminationResponseStatus'):
                for termination_response_status in sirixml_get_elements(response, 'Siri.TerminationSubscriptionResponse.TerminationResponseStatus'):
                    if termination_response_status.Status == True:
                        self._logger.info(f"Terminated subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber} successfully")
                        return True
                    else:
                        self._logger.error(f"Failed to terminate subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber}")
                        return False
            else:
                # publisher returns no termination status at all, that means, there were no subscriptions at publisher side ... good anyway
                self._logger.info(f"Terminated subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber} successfully")
                return True
        else:
            self._logger.error(f"Failed to terminate subscription {subscription.id} @ {subscription.remote_service_participant_ref} as {subscription.subscriber}")
            
    def request(self, publisher_ref: str, method: str = 'POST', headers: dict = dict()) -> bool:

        if self._pubsub:
            raise RuntimeError("Direct requests are only available in request/response mode!")

        # generate SituationExchangeRequest
        request = SituationExchangeRequest(self._service_participant_ref)
        delivery = self._send_direct_request(publisher_ref, request, method, headers)

        if delivery is not None:
            # check whether on_delivery callback is used ...
            if self._on_delivery is not None:
                self._on_delivery(delivery)

            # process service delivery ...
            for pts in sirixml_get_elements(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.Situations.PtSituationElement'):
                situation_id = sirixml_get_value(pts, 'SituationNumber')
                
                result = SituationProgressHandler.handle_situation(pts)

                if result:
                    self._local_node_database.add_or_update_situation(situation_id, pts)
                else:
                    self._local_node_database.remove_situation(situation_id)

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
        endpoint_host = self._service_local_ip_address # self._participant_config.participants[self._service_participant_ref]['host']
        endpoint_port = self._participant_config.participants[self._service_participant_ref]['port']

        uvicorn.run(app=self._endpoint.create_endpoint(
            self._participant_config.participants[self._service_participant_ref]['single_endpoint'],
            self._participant_config.participants[self._service_participant_ref]['delivery_endpoint']
        ), host=endpoint_host, port=endpoint_port)

    def _send_request(self, subscription: Subscription, siri_request: SiriRequest) -> SiriResponse|None:
        try:
            if isinstance(siri_request, CheckStatusRequest):
                status_endpoint = subscription.single_endpoint if subscription.single_endpoint is not None else subscription.status_endpoint
                endpoint = f"{subscription.protocol}://{subscription.host}:{subscription.port}{status_endpoint}"
            elif isinstance(siri_request, SituationExchangeSubscriptionRequest):
                subscribe_endpoint = subscription.single_endpoint if subscription.single_endpoint is not None else subscription.subscribe_endpoint
                endpoint = f"{subscription.protocol}://{subscription.host}:{subscription.port}{subscribe_endpoint}"
            elif isinstance(siri_request, TerminateSubscriptionRequest):
                unsubscribe_endpoint = subscription.single_endpoint if subscription.single_endpoint is not None else subscription.unsubscribe_endpoint
                endpoint = f"{subscription.protocol}://{subscription.host}:{subscription.port}{unsubscribe_endpoint}"
            
            headers = {
                "Content-Type": "application/xml"
            }
            
            response_xml = requests.post(endpoint, headers=headers, data=siri_request.xml())
            response = xml2siri_response(response_xml.content)

            return response
        except Exception as ex:
            self._logger.error(ex)
            return None
        
    def _send_direct_request(self, publisher_ref: str, siri_request: SiriRequest, method: str, headers: dict = dict()) -> SituationExchangeDelivery|None:
        try:
            subscription_host = self._participant_config.participants[publisher_ref]['host']
            subscription_port = self._participant_config.participants[publisher_ref]['port']
            subscription_protocol = self._participant_config.participants[publisher_ref]['protocol']
            
            if isinstance(siri_request, SituationExchangeRequest):
                request_endpoint = self._participant_config.participants[publisher_ref]['single_endpoint'] if self._participant_config.participants[publisher_ref]['single_endpoint'] is not None else self._participant_config.participants[publisher_ref]['request_endpoint']
                endpoint = f"{subscription_protocol}://{subscription_host}:{subscription_port}{request_endpoint}"
            
            siri_headers = {
                "Content-Type": "application/xml"
            }

            if len(headers) > 0:
                siri_headers = siri_headers | headers
            
            if method.lower() == 'post':
                response_xml = requests.post(endpoint, headers=siri_headers, data=siri_request.xml())
            elif method.lower() == 'get':
                response_xml = requests.get(endpoint, headers=siri_headers)
            else:
                raise InvalidMethodError(f"Invalid request method {method}!")
            
            delivery = xml2siri_delivery(response_xml.content)

            return delivery
        except Exception as ex:

            # re-throw occuring InvalidMethodError in this case
            if isinstance(ex, InvalidMethodError):
                raise ex
            else:
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

        self._on_delivery = None

    def set_callbacks(self, on_delivery_callback: typing.Callable[[SiriDelivery], None]|None) -> None:
        self._on_delivery = on_delivery_callback
    
    def create_endpoint(self, single_endpoint: str|None = None, delivery_endpoint: str = '/delivery') -> FastAPI:
        if single_endpoint is not None:
            self._router.add_api_route(single_endpoint, self._dispatcher, methods=['POST'])
        else:
            self._router.add_api_route(delivery_endpoint, self._delivery, methods=['POST'])
        
        self._endpoint.include_router(self._router)

        return self._endpoint
    
    def terminate(self) -> None:
        self._local_node_database.close()
    
    async def _dispatcher(self, req: Request, bgt: BackgroundTasks) -> Response:
        body = str(await req.body())

        if '<ServiceDelivery' in body:
            return await self._delivery(req, bgt)
        else:
            return Response(status_code=400)

    async def _delivery(self, req: Request, bgt: BackgroundTasks) -> Response:
        try:
            delivery = xml2siri_delivery(await req.body())

            # check for active subscriptions from the publisher who has sent the delivery
            delivery_producer_ref = sirixml_get_value(delivery, 'Siri.ServiceDelivery.ProducerRef')
            
            subscription_at_producer_found = False
            for _, subscription in self._local_node_database.get_subscriptions().items():
                if subscription.remote_service_participant_ref == delivery_producer_ref:
                    subscription_at_producer_found = True
                    break

            if not subscription_at_producer_found:
                return Response(status_code=401)
            
            # process service delivery ...
            for pts in sirixml_get_elements(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.Situations.PtSituationElement'):
                situation_id = sirixml_get_value(pts, 'SituationNumber')
                
                result = SituationProgressHandler.handle_situation(pts)

                if result:
                    self._local_node_database.add_or_update_situation(situation_id, pts)
                else:
                    self._local_node_database.remove_situation(situation_id)

            # create data acknowledgement with OK status
            acknowledgement = DataReceivedAcknowledgement(
                sirixml_get_value(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.SubscriberRef'), 
                sirixml_get_value(delivery, 'Siri.ServiceDelivery.ResponseMessageIdentifier')
            )

            acknowledgement.ok()

            # run callback method for delivery
            if self._on_delivery is not None:
                bgt.add_task(self._on_delivery, delivery)

            return Response(content=acknowledgement.xml(), media_type='application/xml')
        except Exception as ex:
            self._logger.error(ex)

            # create data acknowledgement with Fail status
            acknowledgement = DataReceivedAcknowledgement(
                sirixml_get_value(delivery, 'Siri.ServiceDelivery.SituationExchangeDelivery.SubscriberRef'), 
                sirixml_get_value(delivery, 'Siri.ServiceDelivery.ResponseMessageIdentifier')
            )

            acknowledgement.error()

            return Response(content=acknowledgement.xml(), media_type='application/xml')
        
