from ipaddress import IPv4Address
from typing import Union

from pydantic import AnyUrl, BaseModel, validator


class SocketModel(BaseModel):
    name: str
    host: Union[IPv4Address, AnyUrl]
    port: int

    @validator("host")
    def ip_to_string(cls, value):
        return str(value)


class PublisherModel(SocketModel):
    pass


class SubscriberModel(SocketModel):
    topic: str
