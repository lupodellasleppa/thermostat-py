import signal
import zmq

from .validators import PublisherModel, SubscriberModel


signal.signal(signal.SIGINT, signal.SIG_DFL)
context = zmq.Context()


class Socket():
    @classmethod
    def validate(cls, value):

        return cls.validator(**value)

    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port

    def __repr__(self):
        return str(self.__dict__)


class Publisher(Socket):
    validator = PublisherModel

    def __init__(self, name, host, port):
        super().__init__(name, host, port)
        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://{}:{}".format(host, port))

    def send(self, topic, message):
        payload = "{} {}".format(topic, message)
        self.socket.send(payload.encode())


class Subscriber(Socket):
    validator = SubscriberModel

    def __init__(self, name, host, port, topic):
        super().__init__(name, host, port)
        self.topic = topic
        self.socket = context.socket(zmq.SUB)
        self.socket.connect("tcp://{}:{}".format(host, port))
        self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())
        self.socket.RCVTIMEO = 1

    def receive(self):
        message = ""
        try:
            received = self.socket.recv_multipart()
            for payload in received:
                message += payload.decode()
        except zmq.error.Again:
            raise

        return message
