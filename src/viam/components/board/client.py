from datetime import timedelta
from typing import Any, Dict, List, Mapping, Optional

from google.protobuf.duration_pb2 import Duration
from grpclib.client import Channel
from grpclib.client import Stream as ClientStream

from viam.proto.common import DoCommandRequest, DoCommandResponse, Geometry
from viam.proto.component.board import (
    BoardServiceStub,
    GetDigitalInterruptValueRequest,
    GetDigitalInterruptValueResponse,
    GetGPIORequest,
    GetGPIOResponse,
    PowerMode,
    PWMFrequencyRequest,
    PWMFrequencyResponse,
    PWMRequest,
    PWMResponse,
    ReadAnalogReaderRequest,
    SetGPIORequest,
    SetPowerModeRequest,
    SetPWMFrequencyRequest,
    SetPWMRequest,
    StreamTicksRequest,
    StreamTicksResponse,
    WriteAnalogRequest,
)
from viam.resource.rpc_client_base import ReconfigurableResourceRPCClientBase, ResourceRPCClientBase
from viam.streams import StreamWithIterator
from viam.utils import ValueTypes, dict_to_struct, get_geometries, struct_to_dict

from .board import Board, TickStream


class AnalogClient(Board.Analog):
    def __init__(self, name: str, board: "BoardClient"):
        self.board = board
        super().__init__(name)

    async def read(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Board.Analog.Value:
        md = kwargs.get("metadata", ResourceRPCClientBase.Metadata()).proto
        request = ReadAnalogReaderRequest(board_name=self.board.name, analog_reader_name=self.name, extra=dict_to_struct(extra))
        return await self.board.client.ReadAnalogReader(request, timeout=timeout, metadata=md)

    async def write(
        self,
        value: int,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        md = kwargs.get("metadata", ResourceRPCClientBase.Metadata()).proto
        request = WriteAnalogRequest(name=self.board.name, pin=self.name, value=value, extra=dict_to_struct(extra))
        await self.board.client.WriteAnalog(request, timeout=timeout, metadata=md)


class DigitalInterruptClient(Board.DigitalInterrupt):
    def __init__(self, name: str, board: "BoardClient"):
        self.board = board
        super().__init__(name)

    async def value(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> int:
        md = kwargs.get("metadata", ResourceRPCClientBase.Metadata()).proto
        request = GetDigitalInterruptValueRequest(board_name=self.board.name, digital_interrupt_name=self.name, extra=dict_to_struct(extra))
        response: GetDigitalInterruptValueResponse = await self.board.client.GetDigitalInterruptValue(request, timeout=timeout, metadata=md)
        return response.value


class GPIOPinClient(Board.GPIOPin):
    def __init__(self, name: str, board: "BoardClient"):
        self.board = board
        super().__init__(name)

    async def get(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> bool:
        md = kwargs.get("metadata", ResourceRPCClientBase.Metadata()).proto
        request = GetGPIORequest(name=self.board.name, pin=self.name, extra=dict_to_struct(extra))
        response: GetGPIOResponse = await self.board.client.GetGPIO(request, timeout=timeout, metadata=md)
        return response.high

    async def set(
        self,
        high: bool,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        md = kwargs.get("metadata", ResourceRPCClientBase.Metadata()).proto
        request = SetGPIORequest(name=self.board.name, pin=self.name, high=high, extra=dict_to_struct(extra))
        await self.board.client.SetGPIO(request, timeout=timeout, metadata=md)

    async def get_pwm(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> float:
        md = kwargs.get("metadata", ResourceRPCClientBase.Metadata()).proto
        request = PWMRequest(name=self.board.name, pin=self.name, extra=dict_to_struct(extra))
        response: PWMResponse = await self.board.client.PWM(request, timeout=timeout, metadata=md)
        return response.duty_cycle_pct

    async def set_pwm(
        self,
        duty_cycle: float,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        md = kwargs.get("metadata", ResourceRPCClientBase.Metadata()).proto
        request = SetPWMRequest(name=self.board.name, pin=self.name, duty_cycle_pct=duty_cycle, extra=dict_to_struct(extra))
        await self.board.client.SetPWM(request, timeout=timeout, metadata=md)

    async def get_pwm_frequency(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> int:
        md = kwargs.get("metadata", ResourceRPCClientBase.Metadata()).proto
        request = PWMFrequencyRequest(name=self.board.name, pin=self.name, extra=dict_to_struct(extra))
        response: PWMFrequencyResponse = await self.board.client.PWMFrequency(request, timeout=timeout, metadata=md)
        return response.frequency_hz

    async def set_pwm_frequency(
        self,
        frequency: int,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        md = kwargs.get("metadata", ResourceRPCClientBase.Metadata()).proto
        request = SetPWMFrequencyRequest(name=self.board.name, pin=self.name, frequency_hz=frequency, extra=dict_to_struct(extra))
        await self.board.client.SetPWMFrequency(request, timeout=timeout, metadata=md)


class BoardClient(Board, ReconfigurableResourceRPCClientBase):
    """
    gRPC client for the Board component.
    """

    _analog_names: List[str]
    _digital_interrupt_names: List[str]

    def __init__(self, name: str, channel: Channel):
        self.channel = channel
        self.client = BoardServiceStub(channel)
        self._analog_names = []
        self._digital_interrupt_names = []
        super().__init__(name)

    async def analog_by_name(self, name: str) -> Board.Analog:
        self._analog_names.append(name)
        return AnalogClient(name, self)

    async def digital_interrupt_by_name(self, name: str) -> Board.DigitalInterrupt:
        self._digital_interrupt_names.append(name)
        return DigitalInterruptClient(name, self)

    async def gpio_pin_by_name(self, name: str) -> Board.GPIOPin:
        return GPIOPinClient(name, self)

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

    async def set_power_mode(
        self,
        mode: PowerMode.ValueType,
        duration: Optional[timedelta] = None,
        *,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        md = kwargs.get("metadata", self.Metadata()).proto
        duration_pb: Optional[Duration] = None
        if duration is not None:
            duration_pb = [(d, d.FromTimedelta(duration)) for d in [Duration()]][0][0]
        request = SetPowerModeRequest(name=self.name, power_mode=mode, duration=duration_pb)
        await self.client.SetPowerMode(request, timeout=timeout, metadata=md)

    async def get_geometries(self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> List[Geometry]:
        md = kwargs.get("metadata", self.Metadata())
        return await get_geometries(self.client, self.name, extra, timeout, md)

    async def stream_ticks(
        self,
        interrupts: List[Board.DigitalInterrupt],
        *,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> TickStream:
        names = []
        for di in interrupts:
            names.append(di.name)
        request = StreamTicksRequest(name=self.name, pin_names=names, extra=dict_to_struct(extra))

        async def read():
            md = kwargs.get("metadata", self.Metadata()).proto
            tick_stream: ClientStream[StreamTicksRequest, StreamTicksResponse]
            async with self.client.StreamTicks.open(metadata=md) as tick_stream:
                try:
                    await tick_stream.send_message(request, end=True)
                    async for tick in tick_stream:
                        yield tick
                except Exception as e:
                    raise (e)

        return StreamWithIterator(read())
