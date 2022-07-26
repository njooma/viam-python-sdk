from typing import Generic, Type, TypeVar

from grpclib.client import Channel
from viam.proto.api.common import ResourceName
from viam.services.motion import MotionClient
from viam.services.vision import VisionClient

Service = TypeVar('Service')


class ServiceType(Generic[Service]):

    @classmethod
    @property
    def MOTION(cls):
        return ServiceType('motion', MotionClient)

    @classmethod
    @property
    def VISION(cls):
        return ServiceType('vision', VisionClient)

    def __init__(self, name: str, cls: Type[Service]):
        self.resource_name = ResourceName(
            namespace='rdk',
            type='service',
            subtype=name,
            name=name
        )
        self._cls = cls

    @property
    def name(self):
        return self.resource_name.name

    def with_channel(self, channel: Channel) -> Service:
        return self._cls(channel)