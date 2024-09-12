import logging
import asyncio
import subprocess
from typing import List, Union
import pylabrobot
from pylabrobot.liquid_handling.backends.backend import LiquidHandlerBackend


from pylabrobot.liquid_handling.liquid_classes.tecan import TecanLiquidClass, get_liquid_class
from pylabrobot.resources import Liquid, TecanPlate, TecanTip, Resource
from pylabrobot.liquid_handling.standard import Pickup, Drop, Aspiration, Dispense, Move, PickupTipRack, DropTipRack
from tecan import Fluent  # Import the Fluent client

logger = logging.getLogger(__name__)

class FLUENT(LiquidHandlerBackend):
    def __init__(self, server_ip: str, server_port: int, num_channels: int = 8, insecure: bool = False, simulation_mode: bool = False):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self._num_channels = num_channels
        self.simulation_mode = simulation_mode
        self.client = Fluent(server_ip, server_port, insecure=insecure)
        self.connected = False

    async def setup(self):
        try:
            self.client.start_fluent(simulation_mode=self.simulation_mode)
            self.connected = True
            logger.info(f"Connected to Tecan Fluent at {self.server_ip}:{self.server_port} with simulation mode={self.simulation_mode}")
        except Exception as e:
            logger.error(f"Failed to connect to Tecan Fluent: {e}")
            self.connected = False

    async def stop(self):
        try:
            self.client.shutdown(10)
            self.connected = False
            logger.info("Disconnected from Tecan Fluent")
        except Exception as e:
            logger.error(f"Failed to disconnect from Tecan Fluent: {e}")

    @property
    def num_channels(self):
        return self._num_channels

    async def check_channel_availability(self, use_channels: List[int]):
        available_channels = list(range(self.num_channels))
        for channel in use_channels:
            if channel not in available_channels:
                raise RuntimeError(f"Channel {channel} is not available. Available channels: {available_channels}")

    async def pick_up_tips(self, ops: List[Pickup], use_channels: List[int], **backend_kwargs):
        if not self.connected:
            raise RuntimeError("Not connected to Tecan Fluent")
        await self.check_channel_availability(use_channels)
        try:
            for op in ops:
                position = op.resource.get_absolute_location()
                self.client.get_tips(
                    airgap_volume=0,
                    airgap_speed=0,
                    diti_type=op.tip.tip_type.name  # Correctly pass the tip type as a string
                )
                logger.info(f"Picked up tips from {op.resource.name} at position {position}")
        except Exception as e:
            logger.error(f"Failed to pick up tips: {e}")

    async def drop_tips(self, ops: List[Drop], use_channels: List[int], **backend_kwargs):
        if not self.connected:
            raise RuntimeError("Not connected to Tecan Fluent")
        try:
            for op in ops:
                position = op.resource.get_absolute_location()
                self.client.drop_tips(
                    rack_id=op.resource.name,
                    position=(position.x, position.y),
                    channels=use_channels
                )
                logger.info(f"Dropped tips to {op.resource.name} at position {position}")
        except Exception as e:
            logger.error(f"Failed to drop tips: {e}")

    async def aspirate(self, ops: List[Aspiration], use_channels: List[int], **backend_kwargs):
        if not self.connected:
            raise RuntimeError("Not connected to Tecan Fluent")
        for op in ops:
            liquid_class = op.liquids[-1][0] if op.liquids else Liquid.WATER
            self.client.aspirate(op.volume, op.resource.name, liquid_class)

    async def dispense(self, ops: List[Dispense], use_channels: List[int], **backend_kwargs):
        if not self.connected:
            raise RuntimeError("Not connected to Tecan Fluent")
        for op in ops:
            liquid_class = op.liquids[-1][0] if op.liquids else Liquid.WATER
            self.client.dispense(op.volume, op.resource.name, liquid_class)

        tecan_liquid_classes = [
            get_liquid_class(
                target_volume=op.volume,
                liquid_class=op.liquids[-1][0] or Liquid.WATER,
                tip_type=op.tip.tip_type
            ) if isinstance(op.tip, TecanTip) else None for op in ops
        ]

        for op, tlc in zip(ops, tecan_liquid_classes):
            op.volume = tlc.compute_corrected_volume(op.volume) if tlc is not None else op.volume

    async def aspirate96(self, aspiration: Union[TecanPlate, Resource]):
        logger.info("aspirate96 called with %s", aspiration)
        # Add the actual implementation here

    async def dispense96(self, dispense: Union[TecanPlate, Resource]):
        logger.info("dispense96 called with %s", dispense)
        # Add the actual implementation here

    async def drop_tips96(self, drop: DropTipRack):
        logger.info("drop_tips96 called with %s", drop)
        # Add the actual implementation here

    async def move_resource(self, move: Move):
        logger.info("move_resource called with %s", move)
        # Add the actual implementation here

    async def pick_up_tips96(self, pickup: PickupTipRack):
        logger.info("pick_up_tips96 called with %s", pickup)
        # Add the actual implementation here

    async def prepare_method(self, to_prepare: str):
        try:
            # Clear specific directories
            subprocess.run(["cmd.exe", "/c", "rd", "C:/ProgramData/Tecan/VisionX/Journaling/000/", "/q", "/s"], check=True)
            subprocess.run(["cmd.exe", "/c", "rd", "C:/ProgramData/Tecan/VisionX/Journaling/ToDelete/", "/q", "/s"], check=True)
            # Prepare the method
            self.client.prepare_method(to_prepare)
            logger.info(f"Prepared method: {to_prepare}")
        except Exception as e:
            logger.error(f"Failed to prepare method: {e}")

    async def run_method(self):
        try:
            self.client.run_method()
            logger.info("Method running")
        except Exception as e:
            logger.error(f"Failed to run method: {e}")

    async def pause_run(self):
        try:
            self.client.pause_run()
            logger.info("Method paused")
        except Exception as e:
            logger.error(f"Failed to pause method: {e}")

    async def resume_run(self):
        try:
            self.client.resume_run()
            logger.info("Method resumed")
        except Exception as e:
            logger.error(f"Failed to resume method: {e}")

    async def stop_method(self):
        try:
            self.client.stop_method()
            logger.info("Method stopped")
        except Exception as e:
            logger.error(f"Failed to stop method: {e}")

    async def close_method(self):
        try:
            self.client.close_method()
            logger.info("Method closed")
        except Exception as e:
            logger.error(f"Failed to close method: {e}")

    async def set_variable_value(self, variable_name: str, value: str):
        try:
            self.client.set_variable_value(variable_name, value)
            logger.info(f"Set variable {variable_name} to {value}")
        except Exception as e:
            logger.error(f"Failed to set variable {variable_name}: {e}")

    async def get_variable_names(self) -> List[str]:
        try:
            variable_names = self.client.get_variable_names()
            logger.info(f"Variable names: {variable_names}")
            return variable_names
        except Exception as e:
            logger.error(f"Failed to get variable names: {e}")
            return []

    async def get_variable_value(self, variable_name: str) -> str:
        try:
            value = self.client.get_variable_value(variable_name)
            logger.info(f"Value of variable {variable_name}: {value}")
            return value
        except Exception as e:
            logger.error(f"Failed to get variable value for {variable_name}: {e}")
            return ""

    async def get_all_runnable_methods(self) -> List[str]:
        try:
            methods = self.client.get_all_runnable_methods()
            logger.info(f"Runnable methods: {methods}")
            return methods
        except Exception as e:
            logger.error(f"Failed to get all runnable methods: {e}")
            return []
