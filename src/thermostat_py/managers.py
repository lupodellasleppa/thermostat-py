from .sockets import Publisher, Subscriber
from .thermometers import ThermometerWired, ThermometerWireless


class SocketsManager():
    def __init__(self):
        self.publishers = {}
        self.subscribers = {}
        self.objects = {
            "publisher": Publisher,
            "subscriber": Subscriber
        }

    def add(self, kind, value):
        key = kind + "s"
        validated = self.objects[kind].validate(value).dict()
        name = validated["name"]
        self.__dict__[key][name] = self.objects[kind](**validated)

    def remove(self, kind, name):
        key = kind + "s"
        return self.__dict__[key].pop(name)


class ThermometerManager():
    def __init__(self):
        self.wired = {}
        self.wireless = {}
        self.objects = {
            "wired": ThermometerWired,
            "wireless": ThermometerWireless
        }

    def add(self, kind, value):
        validated = self.objects[kind].validate(value).dict()
        print(kind, validated)
        name = validated["name"]
        self.__dict__[kind][name] = self.objects[kind](**validated)

    def remove(self, kind, name):
        return self.__dict__[kind].pop(name)
