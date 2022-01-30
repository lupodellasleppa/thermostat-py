from enum import Enum
from ipaddress import IPv4Address
from typing import Union

from pydantic import AnyUrl, BaseModel, validator


class ThermometerTypeEnum(str, Enum):
    wired = "wired"
    wireless = "wireless"


class ThermometerModel(BaseModel):
    name: str
    description: str = None
    read_period: int
    thermometer_type: str
    target_temperature: int = None


class ThermometerWiredModel(ThermometerModel):
    pass


class ThermometerWirelessModel(ThermometerModel):
    host: Union[IPv4Address, AnyUrl]
    port: int
    send_period: int
    timeout: int

    @validator("host")
    def ip_to_string(cls, value):
        return str(value)
