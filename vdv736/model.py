from typing import Any
from lxml.etree import tostring
from lxml.objectify import fromstring
from lxml.objectify import Element
from lxml.objectify import ObjectifiedElement


class Subscription:

    @classmethod
    def create(cls, id: str, host: str, port: int, protocol: str, subscriber: str, termination: str):

        obj = cls()
        obj.id = id
        obj.host = host
        obj.port = port
        obj.protocol = protocol
        obj.subscriber = subscriber
        obj.termination = termination

        return obj

    @classmethod
    def serialize(cls, obj) -> str:
        element = Element('subscription')
        element.id = obj.id
        element.host = obj.host
        element.port = obj.port
        element.protocol = obj.protocol
        element.subscriber = obj.subscriber
        element.termination = obj.termination

        element.remote_service_participant_ref = obj.remote_service_participant_ref
        element.remote_service_startup_time = obj.remote_service_startup_time

        element.single_endpoint = obj.single_endpoint
        element.status_endpoint = obj.status_endpoint
        element.subscribe_endpoint = obj.subscribe_endpoint
        element.unsubscribe_endpoint = obj.unsubscribe_endpoint

        return tostring(element)
    
    @classmethod
    def unserialize(cls, xml: str):
        element = fromstring(xml)

        obj = cls()
        obj.id = element.id.text
        obj.host = element.host.text
        obj.port = element.port.text
        obj.protocol = element.protocol.text
        obj.subscriber = element.subscriber.text
        obj.termination = element.termination.text

        obj.remote_service_participant_ref = element.remote_service_participant_ref.text
        obj.remote_service_startup_time = element.remote_service_startup_time.text

        obj.single_endpoint = element.single_endpoint.text
        obj.status_endpoint = element.status_endpoint.text
        obj.subscribe_endpoint = element.subscribe_endpoint.text
        obj.unsubscribe_endpoint = element.unsubscribe_endpoint.text

        return obj
    
    def __init__(self):
        self.id = None
        self.host = None
        self.port = None
        self.protocol = None
        self.subscriber = None
        self.termination = None

        self.remote_service_participant_ref = None
        self.remote_service_startup_time = None

        self.single_endpoint = None
        self.status_endpoint = '/status'
        self.subscribe_endpoint = '/subscribe'
        self.unsubscribe_endpoint = '/unsubscribe'


class PublicTransportSituation(ObjectifiedElement):
    
    @classmethod
    def create(cls, id: str):

        obj = cls()
        obj.tag = 'PtSituationElement'

        obj.SituationNumber = id

        return obj
    
    @classmethod
    def serialize(cls, obj) -> str:
        return tostring(obj)
    
    @classmethod
    def unserialize(cls, xml: str):
        obj = fromstring(xml)
        return obj
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __eq__(self, other):
        return self.equals(other)

    def __copy__(self):
        return PublicTransportSituation(super().__copy__())

    def __deepcopy__(self, memo=None):
        return PublicTransportSituation(super().__deepcopy__(memo))