# PyVDV736
Simple reference implementation for [VDV736](https://www.vdv.de/736-2-sds.pdfx?forced=true) subscriber and publisher written in Python. [VDV736](https://www.vdv.de/736-2-sds.pdfx?forced=true) is a data standard based on [SIRI-SX](https://github.com/SIRI-CEN/SIRI) for public transport situation exchange.

## Situation Exchange in VDV736
Exchanging public transport situations works with a realtime capable setup using a publish/subscribe mechanism. To get this working, the publisher (in most cases called 'server') as well as the subscriber (in most cases called 'client') needs to be callable via an HTTP(S) interface.

A subscription then works as follows:
- The subscriber registers at the publisher with its participant ID (aka 'Leitstellenkennung') and some basic subscription parameters
- The publisher stores this subscription and every time a new public transport situation is published, the publisher calls the subscriber's endpoint with a body containing data
- At the end, the subscribers terminates his subscription sending a request to the publisher again, stating that the existing subscription should be deleted

This way, data are only transferred, when they're updated in realtime without polling. Other well-known public transport protocols (like VDV453, VDV454, SIRI) work exactly the same. A digital data hub (aka 'Datendrehscheibe') combines the role of the publisher and subscriber.

An alertnative to this publish/subscribe mechanism is the request/response pattern: Using this pattern, a client simply requests data updates periodically but *is not notified when new data are available*. Hence, request/response is not realtime capable, but much easier to implement in a production environment, as no participant IDs and system configurations besides a request URL must be exchanged.

### Differences to SIRI-SX
- SIRI-SX offers also the option for fetching public transport situations using a simple GET request. VDV736 states that only publish/subscribe is supported. Hence, the request endpoint of the publisher is only experimental and not supported officially.
- SIRI services offer a so-called fetched delivery. In this mode, a producer notifies the consumer with a `DataReadyNotification` that there're new data available and the subscriber states that he's ready to receive the data with a `FetchDataRequest`. This mode is currently not supported in this repository.
- SIRI services have normally implemented a heartbeat request. This request is compareable to the status request, the difference here is that the heartbeat request is triggered by each instance actively, where the status request is performed by the opposide participant and the called instance is only answering passively.

## Configuration
There's a YAML file which contains basic configuration for all participants (subscriber as well as publisher). See following example for reference:

```yaml
PY_TEST_PUBLISHER:
  host: "127.0.0.1"
  port: 9091
  protocol: http
  single_endpoint: null
  status_endpoint: /status
  subscribe_endpoint: /subscribe
  unsubscribe_endpoint: /unsubscribe
  request_endpoint: /request
  delivery_endpoint: null
```

The top level keys are the participant IDs, which must be agreed between the participants at first. Each participant system needs to have an IP address or hostname, a port and a protocol which should be used for access. You can also specify the endpoints for the different actions a participant is providing.

_Note: There're some implementations which do not use special endpoints for each request type. To deal with them, set the property `single_endpoint` to a value other than `null`. This leads to the other endpoint configurations to become ignored and works for remote publishers as well as for the subscriber and publisher in this implementation._

## Installation & Usage
Using this library is quite simple. Install it using

`pip install pyvdv736`

Then use a `Subscriber` or `Publisher` object to work with. See following example:

```python
from vdv736.subscriber import Subscriber
from vdv736.delivery import SiriDelivery

def on_delivery(delivery: SiriDelivery) -> None:
    print('Delivery callback called...')

with Subscriber('PY_TEST_SUBSCRIBER', './participants.yaml') as subscriber:
    subscriber.set_callbacks(on_delivery)
    
    subscription_id = subscriber.subscribe('PY_TEST_PUBLISHER')
    ...
    subscriber.unsubscribe(subscription_id)

    while True:
        pass
```

You can also use the subscriber in the request/response pattern this way:

```python
from vdv736.subscriber import Subscriber
from vdv736.delivery import SiriDelivery

def on_delivery(delivery: SiriDelivery) -> None:
    print('Delivery callback called...')

with Subscriber('PY_TEST_SUBSCRIBER', './participants.yaml', publish_subscribe=False) as subscriber:
    
    # run a direct request on the subscriber
    # the on_delivery callback is called immediately afterwards
    subscriber.request('PY_TEST_PUBLISHER')

    # alternatively you can process every single situation using the method get_situations() and a for loop
    for situation_id, situation in subscriber.get_situations().items():
        pass # or to whatever you want to do ...

    while True:
        pass
```

Please note the keyword argument `publish_subscribe` set to `False` here in order to use request/response pattern.

According to VDV736, all request must be performed using request method `POST`. However there're some data platforms providing ([OpenTransportData Swiss](https://opentransportdata.swiss/de/cookbook/siri-sx/)) SIRI-SX like data using the `GET` method. You can perform GET requests with custom headers using the following snippet:

```python
hdr = {
    'Authorization': '[YourAccessToken]'
}

subscriber.request('PY_TEST_PUBLISHER', './participants.yaml', publish_subscribe=False, method='GET', headers=hdr)

for situation_id, situation in subscriber.get_situations().items():
    pass
```

_Please be aware, that `GET` requests are not supported officially!_

See sample other scripts in the [demo](/demo) folder.

## License
This project is licensed under the Apache License. See [LICENSE.md](LICENSE.md) for more information.