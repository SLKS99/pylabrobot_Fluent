import logging
import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends.tecan.FLUENT import FLUENT
from pylabrobot.resources import Fluent780Deck, PCR_Plate_96_Well, DiTi_50ul_Te_MO, Nest_61mm_6Pos, DiTi_Nest_4_pos_FCA
from pylabrobot.liquid_handling.standard import Pickup, Drop, Aspiration, Dispense

async def run_simulation():
    try:
        print("Running simulation...")

        # Set up the Fluent backend
        fluent = FLUENT(simulation_mode=True)
        await fluent.setup()

        # Set up the deck
        deck = Fluent780Deck()
        lh = LiquidHandler(backend=fluent, deck=deck)

        # Add labware to the deck
        source_plate = PCR_Plate_96_Well("source_plate")
        dest_plate = PCR_Plate_96_Well("dest_plate")
        tip_rack = DiTi_50ul_Te_MO("tip_rack")

        deck.assign_child_resource(source_plate, "11")
        deck.assign_child_resource(dest_plate, "22")
        deck.assign_child_resource(tip_rack, "34")

        await lh.setup()

        # Perform liquid handling operations
        tips = tip_rack.get_tips(["A1", "A2", "A3", "A4"])
        await lh.pick_up_tips(tips)

        # Multi-volume aspiration
        source_wells = source_plate.get_wells(["A1", "A2", "A3", "A4"])
        aspirate_volumes = [10, 20, 30, 40]  # Different volumes for each tip
        aspirations = [Aspiration(source_wells[i], aspirate_volumes[i], tips[i]) for i in range(4)]
        await lh.aspirate(aspirations)

        # Multi-volume dispense
        dest_wells = dest_plate.get_wells(["A1", "A2", "A3", "A4"])
        dispense_volumes = [10, 20, 30, 40]  # Different volumes for each tip
        dispenses = [Dispense(dest_wells[i], dispense_volumes[i], tips[i]) for i in range(4)]
        await lh.dispense(dispenses)

        # Drop tips
        await lh.drop_tips(tips)

        print("Simulation completed successfully.")

    except Exception as e:
        print(f"An error occurred during simulation: {e}")
    finally:
        await fluent.stop()  # Ensure the system is stopped even if an error occurs

if __name__ == "__main__":
    import runpy
    import os
    import sys

    # Add the parent directory to sys.path
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    sys.path.insert(0, parent_dir)

    # Run the current file as a module
    runpy.run_module('pylabrobot.liquid_handling.backends.tecan.tecan_fluent', run_name='__main__')
else:
    # This block will be executed when the file is imported as a module
    asyncio.run(run_simulation())