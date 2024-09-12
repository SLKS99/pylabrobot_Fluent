import logging
from typing import List, Union
from pylabrobot.liquid_handling.backends.backend import LiquidHandlerBackend
from tecan import Fluent, DiTi  # Import your SiLA Fluent Client commands (customized from your provided code)
from pylabrobot.liquid_handling.standard import Pickup, Drop, Aspiration, Dispense


logger = logging.getLogger(__name__)

class FLUENT(LiquidHandlerBackend):
    def __init__(self, server_ip: str = "127.0.0.1", server_port: int = 50052, num_channels: int = 8, simulation_mode: bool = False):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self._num_channels = num_channels
        self.simulation_mode = simulation_mode
        self.client = Fluent(server_ip=self.server_ip, server_port=self.server_port)
        self.connected = False

    async def setup(self):
        try:
            self.client.start_fluent(simulation_mode=self.simulation_mode)
            self.connected = True
            logger.info(f"Connected to Fluent SiLA2 at {self.server_ip}:{self.server_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Fluent SiLA2: {e}")
            self.connected = False

    async def stop(self):
        try:
            self.client.shutdown(10)
            self.connected = False
            logger.info("Disconnected from Fluent SiLA2")
        except Exception as e:
            logger.error(f"Failed to disconnect from Fluent SiLA2: {e}")

    async def check_channel_availability(self, use_channels: List[int]):
        available_channels = list(range(self.num_channels))
        for channel in use_channels:
            if channel not in available_channels:
                raise RuntimeError(f"Channel {channel} is not available. Available channels: {available_channels}")

    # PICK UP TIPS
    async def pick_up_tips(self, ops: List[Pickup], use_channels: List[int], **backend_kwargs):
        if not self.connected:
            raise RuntimeError("Not connected to Fluent SiLA2")
        await self.check_channel_availability(use_channels)

        try:
            for op in ops:
                # Use SiLA2 GetTips command
                self.client.get_tips(airgap_volume=0, airgap_speed=0, diti_type=op.tip.tip_type.name)
                logger.info(f"Picked up tips from {op.resource.name}")
        except Exception as e:
            logger.error(f"Failed to pick up tips: {e}")

    # DROP TIPS
    async def drop_tips(self, ops: List[Drop], use_channels: List[int], **backend_kwargs):
        if not self.connected:
            raise RuntimeError("Not connected to Fluent SiLA2")
        await self.check_channel_availability(use_channels)

        try:
            for op in ops:
                # Use SiLA2 DropTips command
                self.client.drop_tips(labware=op.resource.name)
                logger.info(f"Dropped tips to {op.resource.name}")
        except Exception as e:
            logger.error(f"Failed to drop tips: {e}")

    # ASPIRATE with different volumes for each pipette
    async def aspirate(self, ops: List[Aspiration], use_channels: List[int], **backend_kwargs):
        if not self.connected:
            raise RuntimeError("Not connected to Fluent SiLA2")
        await self.check_channel_availability(use_channels)

        try:
            for op in ops:
                # Handle different volumes for each channel
                volumes = [op.volume for _ in use_channels] if isinstance(op.volume, (int, float)) else op.volume

                # Ensure that the number of volumes matches the number of channels used
                if len(volumes) != len(use_channels):
                    raise ValueError("Number of volumes must match the number of channels used")

                # Use SiLA2 Aspirate command with variable volumes
                self.client.aspirate(volume=volumes, labware=op.resource.name, liquid_class="Water", well_offset=0)
                logger.info(f"Aspirated {volumes} from {op.resource.name}")
        except Exception as e:
            logger.error(f"Failed to aspirate: {e}")

    # DISPENSE with different volumes for each pipette
    async def dispense(self, ops: List[Dispense], use_channels: List[int], **backend_kwargs):
        if not self.connected:
            raise RuntimeError("Not connected to Fluent SiLA2")
        await self.check_channel_availability(use_channels)

        try:
            for op in ops:
                # Handle different volumes for each channel
                volumes = [op.volume for _ in use_channels] if isinstance(op.volume, (int, float)) else op.volume

                # Ensure that the number of volumes matches the number of channels used
                if len(volumes) != len(use_channels):
                    raise ValueError("Number of volumes must match the number of channels used")

                # Use SiLA2 Dispense command with variable volumes
                self.client.dispense(volume=volumes, labware=op.resource.name, liquid_class="Water", well_offset=0)
                logger.info(f"Dispensed {volumes} to {op.resource.name}")
        except Exception as e:
            logger.error(f"Failed to dispense: {e}")

    # LABWARE MOVEMENT
    async def move_resource(self, resource_name: str, target_location: str, rotation: int = 0, position: int = 0):
        try:
            self.client.set_location(labware=resource_name, rotation=rotation, target_location=target_location, target_site=position)
            logger.info(f"Moved {resource_name} to {target_location}")
        except Exception as e:
            logger.error(f"Failed to move resource: {e}")

    # ADD LABWARE
    async def add_labware(self, labware_name: str, labware_type: str, target_location: str):
        try:
            self.client.add_labware(labware_name, labware_type, target_location)
            logger.info(f"Added labware: {labware_name} of type {labware_type}")
        except Exception as e:
            logger.error(f"Failed to add labware: {e}")

    # REMOVE LABWARE
    async def remove_labware(self, labware_name: str):
        try:
            self.client.remove_labware(labware_name)
            logger.info(f"Removed labware: {labware_name}")
        except Exception as e:
            logger.error(f"Failed to remove labware: {e}")

    # PREPARE AND RUN METHODS
    async def prepare_method(self, method_name: str):
        try:
            self.client.prepare_method(method_name)
            logger.info(f"Method {method_name} prepared")
        except Exception as e:
            logger.error(f"Failed to prepare method: {e}")

    async def run_method(self):
        try:
            self.client.run_method()
            logger.info("Method running")
        except Exception as e:
            logger.error(f"Failed to run method: {e}")

    async def stop_method(self):
        try:
            self.client.stop_method()
            logger.info("Method stopped")
        except Exception as e:
            logger.error(f"Failed to stop method: {e}")
