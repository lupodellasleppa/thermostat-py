from sockets import Subscriber


class Thermostat():
    def __init__(self):
        self.topics = {
            "subscribers": [
                {
                    "name": "thermometers",
                    "children": [
                        {
                            "name": "hall",
                            "host": "",
                            "port": 5555
                        }
                    ]
                }
            ]
        }

    def create_subscriber(self, host, port, topic):
        return Subscriber(host, port, topic)

    def receive(self, source)
