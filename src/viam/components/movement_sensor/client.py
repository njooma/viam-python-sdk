from typing import Any, Dict, List, Mapping, Optional, Tuple

from grpclib.client import Channel

from viam.components.movement_sensor.movement_sensor import MovementSensor
from viam.proto.common import DoCommandRequest, DoCommandResponse, Geometry, GetReadingsRequest, GetReadingsResponse
from viam.proto.component.movementsensor import (
    GetAccuracyRequest,
    GetAngularVelocityRequest,
    GetAngularVelocityResponse,
    GetCompassHeadingRequest,
    GetCompassHeadingResponse,
    GetLinearAccelerationRequest,
    GetLinearAccelerationResponse,
    GetLinearVelocityRequest,
    GetLinearVelocityResponse,
    GetOrientationRequest,
    GetOrientationResponse,
    GetPositionRequest,
    GetPositionResponse,
    GetPropertiesRequest,
    GetPropertiesResponse,
    MovementSensorServiceStub,
)
from viam.resource.rpc_client_base import ReconfigurableResourceRPCClientBase
from viam.utils import SensorReading, ValueTypes, dict_to_struct, get_geometries, sensor_readings_value_to_native, struct_to_dict

from . import GeoPoint, Orientation, Vector3


class MovementSensorClient(MovementSensor, ReconfigurableResourceRPCClientBase):
    """gRPC client for the MovementSensor component."""

    def __init__(self, name: str, channel: Channel):
        self.channel = channel
        self.client = MovementSensorServiceStub(channel)
        super().__init__(name)

    async def get_position(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Tuple[GeoPoint, float]:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = GetPositionRequest(name=self.name, extra=dict_to_struct(extra))
        response: GetPositionResponse = await self.client.GetPosition(request, timeout=timeout, metadata=md)
        return response.coordinate, response.altitude_m

    async def get_linear_velocity(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Vector3:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = GetLinearVelocityRequest(name=self.name, extra=dict_to_struct(extra))
        response: GetLinearVelocityResponse = await self.client.GetLinearVelocity(request, timeout=timeout, metadata=md)
        return response.linear_velocity

    async def get_angular_velocity(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Vector3:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = GetAngularVelocityRequest(name=self.name, extra=dict_to_struct(extra))
        response: GetAngularVelocityResponse = await self.client.GetAngularVelocity(request, timeout=timeout, metadata=md)
        return response.angular_velocity

    async def get_linear_acceleration(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Vector3:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = GetLinearAccelerationRequest(name=self.name, extra=dict_to_struct(extra))
        response: GetLinearAccelerationResponse = await self.client.GetLinearAcceleration(request, timeout=timeout, metadata=md)
        return response.linear_acceleration

    async def get_compass_heading(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> float:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = GetCompassHeadingRequest(name=self.name, extra=dict_to_struct(extra))
        response: GetCompassHeadingResponse = await self.client.GetCompassHeading(request, timeout=timeout, metadata=md)
        return response.value

    async def get_orientation(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Orientation:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = GetOrientationRequest(name=self.name, extra=dict_to_struct(extra))
        response: GetOrientationResponse = await self.client.GetOrientation(request, timeout=timeout, metadata=md)
        return response.orientation

    async def get_properties(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> MovementSensor.Properties:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = GetPropertiesRequest(name=self.name, extra=dict_to_struct(extra))
        response: GetPropertiesResponse = await self.client.GetProperties(request, timeout=timeout, metadata=md)
        return MovementSensor.Properties.from_proto(response)

    async def get_accuracy(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> MovementSensor.Accuracy:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = GetAccuracyRequest(name=self.name, extra=dict_to_struct(extra))
        return await self.client.GetAccuracy(request, timeout=timeout, metadata=md)

    async def get_readings(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, SensorReading]:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = GetReadingsRequest(name=self.name, extra=dict_to_struct(extra))
        response: GetReadingsResponse = await self.client.GetReadings(request, timeout=timeout, metadata=md)

        return sensor_readings_value_to_native(response.readings)

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, ValueTypes]:
        md = kwargs.get("metadata", self.Metadata()).proto
        request = DoCommandRequest(name=self.name, command=dict_to_struct(command))
        response: DoCommandResponse = await self.client.DoCommand(request, timeout=timeout, metadata=md)
        return struct_to_dict(response.result)

    async def get_geometries(self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> List[Geometry]:
        md = kwargs.get("metadata", self.Metadata())
        return await get_geometries(self.client, self.name, extra, timeout, md)
