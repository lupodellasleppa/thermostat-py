import logging
import time

import pytest

from thermostat_py.sockets import Publisher, SocketsManager, Subscriber


logger = logging.getLogger("test_sockets")


@pytest.fixture
def publisher():
    return Publisher


@pytest.fixture
def subscriber():
    return Subscriber


@pytest.fixture
def socket_manager():
    return SocketsManager


def pub_send(publisher, n):
    logger.info("gon send {} {}".format("-" * 88, n))
    publisher.send("status", "5")
    logger.info("done send")


def sub_receive(publisher, subscriber):
    logger.info("gon receive")
    message = b""
    s = time.perf_counter()
    tt = 100
    n = 2
    c = 1
    r = 1
    while not message:
        logger.info("C = {}".format(c))
        try:
            message = subscriber.receive()
        except Exception:
            if not c % r:
                logger.info("c % {} {}".format(r, c))
                pub_send(publisher, n)
                n += 1
            logger.info("receive failed")
            c += 1
    tt = time.perf_counter() - s
    logger.info("done receive: '{}' in {}".format(message, tt))
    assert tt < 100


def test_pubsub(publisher, subscriber):
    s = Subscriber("subscriber", "localhost", 5555, "status")
    # time.sleep(1)
    p = Publisher("publisher", "*", 5555)
    pub_send(p, 1)
    # time.sleep(1)
    sub_receive(p, s)


def test_socket_manager(publisher, socket_manager, subscriber):
    sm = socket_manager()
    publisher_values = {
        "name": "publisher",
        "host": "127.0.0.1",
        "port": 5555
    }
    subscriber_values = {
        "name": "subscriber",
        "host": "127.0.0.1",
        "port": 5555,
        "topic": "asd"
    }
    sm.add("publisher", publisher_values)
    sm.add("subscriber", subscriber_values)

    for name, publisher in sm.publishers.items():
        logger.info("Publisher: {}".format(publisher))
        assert isinstance(publisher, Publisher)
    for name, subscriber in sm.subscribers.items():
        logger.info("Subscriber: {}".format(subscriber))
        assert isinstance(subscriber, Subscriber)

    sm.remove("publisher", publisher_values["name"])
    sm.remove("subscriber", subscriber_values["name"])

    assert not sm.publishers
    assert not sm.subscribers
