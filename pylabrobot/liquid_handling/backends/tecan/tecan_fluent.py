import logging
import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot_Fluent.pylabrobot.liquid_handling.backends.tecan.FLUENT import FLUENT
from pylabrobot.resources import Fluent780Deck, PCR_Plate_96_Well, DiTi_50ul_Te_MO, Nest_61mm_6Pos, DiTi_Nest_4_pos_FCA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Set up the Tecan Fluent backend
    backend = FLUENT(server_ip="127.0.0.1", server_port=50052, insecure=True, simulation_mode=True, num_channels=8)
    await backend.setup()

    try:
        # Set up the deck
        deck = Fluent780Deck()
        lh = LiquidHandler(backend=backend, deck=deck)

        # Define resources
        pcr_plate = PCR_Plate_96_Well("pcr_plate", with_lid=False)
        diti_rack = DiTi_Nest_4_pos_FCA("diti_rack")
        nest = Nest_61mm_6Pos("nest")

        # Add resources to the deck using the correct method
        deck.assign_child_resource(pcr_plate, rails=10)
        deck.assign_child_resource(diti_rack, rails=20)
        deck.assign_child_resource(nest, rails=30)

        await lh.setup()

        logger.info("Deck setup complete with resources added")

        # Prepare a method
        await backend.prepare_method("test Method")

        # Set and get variable values
        await backend.set_variable_value("test_variable", "new_value")
        variable_names = await backend.get_variable_names()
        for name in variable_names:
            value = await backend.get_variable_value(name)
            logger.info(f"Variable {name}: {value}")

    finally:
        # Disconnect from Tecan Fluent
        await backend.stop()

# Run the test
asyncio.run(main())
