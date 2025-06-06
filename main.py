# main.py
import time
import pymem
import sys
import logging

import config
import memory
import input_handler
import hacks
from entities import ResolvedAddresses


def run():
    mem_manager = memory.MemoryManager(config.PROCESS_NAME)
    current_addresses: ResolvedAddresses | None = None
    last_resolve_time = 0

    config.app_config = config.Configuration()  # Initialize config
    pointerResolutionFailed: bool = True

    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("trove_mod_tool.log"), logging.StreamHandler(sys.stdout)],
        force=True,
        encoding="utf-8",
    )

    logging.info("--==* Trove Modification Tool *==--")
    logging.info("- F3: Toggle Hack")
    logging.info("- F4: Change Hack Mode (AccelBoost/Fly)")
    logging.info("- PgUp: Increase Speed")
    logging.info("- PgDown: Decrease Speed")
    logging.info("--===============================--")

    try:
        input_handler.setup_hotkeys()

        while True:
            # --- Process Connection Management ---
            if not mem_manager.is_attached():
                memory.wait_for_process(config.PROCESS_NAME)
                if not mem_manager.attach():
                    logging.warning("Failed to attach to process. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue  # Retry attaching
                # Reset state on successful attach/reattach
                current_addresses = None
                last_resolve_time = 0

            # Check if process is still running
            if not memory.is_process_running(config.PROCESS_NAME):
                logging.info("Target process has closed.")
                mem_manager.detach()
                continue  # Go back to waiting for process

            # --- Pointer Resolution ---
            current_time = time.time()
            if not current_addresses or (current_time - last_resolve_time > config.POINTER_RESOLVE_INTERVAL_S):
                resolved = mem_manager.resolve_addresses()

                if not resolved:
                    pointerResolutionFailed = True
                    current_addresses = None
                    logging.warning("Failed to resolve pointers. Retrying...")
                    time.sleep(1)
                    continue

                current_addresses = resolved
                last_resolve_time = current_time
                if pointerResolutionFailed:
                    pointerResolutionFailed = False
                    logging.info("Successfully resolved pointers.")

            # --- Hack Application Logic ---
            if config.app_config.hack_on and current_addresses:
                foreground_pid = memory.get_foreground_process_pid()
                is_target_active = foreground_pid is not None and foreground_pid == mem_manager.process_id

                if is_target_active:
                    try:
                        if config.app_config.current_hack == config.HackMode.ACCELBOOST:
                            hacks.apply_accelboost(mem_manager, current_addresses)
                        elif config.app_config.current_hack == config.HackMode.FLY:
                            hacks.apply_fly(mem_manager, current_addresses)

                        # --- Noclip Bypass Logic ---
                        is_actively_moving = mem_manager.is_moving(current_addresses)
                        mem_manager.update_noclip_patch(should_be_moving=is_actively_moving)

                    except (pymem.exception.MemoryReadError, pymem.exception.MemoryWriteError) as e:
                        logging.error(f"Memory access error during hack loop: {e}. Detaching...")
                        mem_manager.detach()  # Detach on critical memory error
                        current_addresses = None  # Force re-resolve after reattach
                    except Exception as e:
                        logging.error(f"Unexpected error in hack loop: {e}")

            # --- Loop Timing ---
            time.sleep(config.INTERVAL_MS / 1000.0)

    except KeyboardInterrupt:
        logging.info("\nCtrl+C detected. Exiting...")
    except Exception as e:
        logging.error(f"\nAn unhandled exception occurred: {e}")
    finally:
        logging.info("Cleaning up...")
        input_handler.remove_hotkeys()
        if mem_manager.is_attached():
            mem_manager.detach()
        logging.info("Exited.")


if __name__ == "__main__":
    run()
