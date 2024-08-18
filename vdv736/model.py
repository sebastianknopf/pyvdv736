from lxml.etree import tostring
from lxml.objectify import fromstring
from lxml.objectify import Element
from lxml.objectify import ObjectifiedElement


class Subscription:

    @classmethod
    def create(cls, id: str, host: str, port: int, subscriber: str, termination: str):

        obj = cls()
        obj.id = id
        obj.host = host
        obj.port = port
        obj.subscriber = subscriber
        obj.termination = termination

        return obj

    @classmethod
    def serialize(cls, obj) -> str:
        element = Element('subscription')
        element.id = obj.id
        element.host = obj.host
        element.port = obj.port
        element.subscriber = obj.subscriber
        element.termination = obj.termination

        element.status_endpoint = obj.status_endpoint
        element.subscribe_endpoint = obj.subscribe_endpoint
        element.unsubscribe_endpoint = obj.unsubscribe_endpoint

        return tostring(element)
    
    @classmethod
    def unserialize(cls, xml: str):
        element = fromstring(xml)

        obj = cls()
        obj.id = element.id
        obj.host = element.host
        obj.port = element.port
        obj.subscriber = element.subscriber
        obj.termination = element.termination

        obj.status_endpoint = element.status_endpoint
        obj.subscribe_endpoint = element.subscribe_endpoint
        obj.unsubscribe_endpoint = element.unsubscribe_endpoint

        return obj
    
    def __init__(self):
        self.id = None
        self.host = None
        self.port = None
        self.subscriber = None
        self.termination = None

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