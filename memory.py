# memory.py
import pymem
import pymem.process
import pymem.pattern
import pymem.exception
import psutil
import re
import time
import win32process
import win32gui
import pywintypes
import logging
from typing import Optional

import config
from entities import ResolvedAddresses


class MemoryManager:
    def __init__(self, process_name: str):
        self.process_name = process_name
        self.pm: Optional[pymem.Pymem] = None
        self.process_id: Optional[int] = None
        self.module_base: Optional[int] = None
        self.noclip_address: Optional[int] = None
        self._is_noclip_patched: bool = False

    def attach(self) -> bool:
        try:
            self.pm = pymem.Pymem(self.process_name)
            self.process_id = self.pm.process_id
            module = pymem.process.module_from_name(self.pm.process_handle, self.process_name)
            if not module:
                logging.error(f"Error: Could not find module {self.process_name}")
                self.pm = None
                return False
            self.module_base = module.lpBaseOfDll
            logging.info(f"Successfully attached to {self.process_name} (PID: {self.process_id}), Base: {hex(self.module_base)}")
            self._find_noclip_address(module)
            return True
        except pymem.exception.ProcessNotFound:
            self.pm = None
            self.process_id = None
            self.module_base = None
            logging.error(f"Error: Process {self.process_name} not found.")
            return False
        except Exception as e:
            self.pm = None
            self.process_id = None
            self.module_base = None
            logging.error(f"Error attaching to process: {e}")
            return False

    def detach(self):
        if self.pm:
            try:
                # Restore noclip bytes if patched before closing
                if self.noclip_address and self._is_noclip_patched:
                    self.write_bytes(self.noclip_address, config.ORIGINAL_NOCLIP_BYTES)
                    self._is_noclip_patched = False
                    logging.info("[Bypass] Restored original bytes on detach.")
                self.pm.close_process()
            except Exception as e:
                logging.error(f"Error during detach: {e}")
            finally:
                self.pm = None
                self.process_id = None
                self.module_base = None
                self.noclip_address = None
                logging.info("Detached from process.")

    def is_attached(self) -> bool:
        return self.pm is not None and self.process_id is not None

    def _read_uint(self, address: int) -> Optional[int]:
        if not self.pm:
            return None
        try:
            return self.pm.read_uint(address)
        except (pymem.exception.MemoryReadError, TypeError, ValueError):
            return None

    def read_float(self, address: int) -> Optional[float]:
        if not self.pm:
            return None
        try:
            return self.pm.read_float(address)
        except (pymem.exception.MemoryReadError, TypeError, ValueError):
            return None

    def write_float(self, address: int, value: float) -> bool:
        if not self.pm:
            return False
        try:
            self.pm.write_float(address, value)
            return True
        except (pymem.exception.MemoryWriteError, TypeError, ValueError):
            return False

    def write_bytes(self, address: int, value: bytes) -> bool:
        if not self.pm:
            return False
        try:
            self.pm.write_bytes(address, value, len(value))
            return True
        except (pymem.exception.MemoryWriteError, TypeError, ValueError):
            return False

    def _resolve_pointer_chain(self, base_address: int, offsets: list[int]) -> Optional[int]:
        if not self.pm:
            return False
        try:
            addr = base_address
            for offset in offsets:
                addr = self._read_uint(addr + offset)
                if addr is None:
                    logging.error(f"Pointer chain failed at offset '{offset}'.")
                    return None
        except (pymem.exception.MemoryReadError, TypeError, ValueError):
            logging.error("Error resolving pointer chain")
            return False
        return addr

    def resolve_addresses(self) -> Optional[ResolvedAddresses]:
        if not self.pm or not self.module_base:
            return None

        try:
            # Read the initial static pointer relative to the module base
            chain_start_addr = self._read_uint(self.module_base + config.STATIC_POINTER_START_OFFSET)
            if not chain_start_addr:
                logging.error("Failed to read chain start address")
                return None

            # Resolve Velocity Pointers
            coord_vel_base_addr = self._resolve_pointer_chain(chain_start_addr, config.VELOCITY_OFFSETS)
            if not coord_vel_base_addr:
                logging.error("Failed to resolve velocity base address")
                return None


            # Resolve Camera Pointers
            cam_base_addr = self._resolve_pointer_chain(chain_start_addr, config.CAMERA_OFFSETS)
            if not cam_base_addr:
                logging.error("Failed to resolve camera base address.")
                return None

            return ResolvedAddresses(
                velocity_x=coord_vel_base_addr + 0xB0,
                velocity_y=coord_vel_base_addr + 0xB4,
                velocity_z=coord_vel_base_addr + 0xB8,
                camera_x=cam_base_addr + 0x100,
                camera_y=cam_base_addr + 0x104,
                camera_z=cam_base_addr + 0x108,
            )
        except (pymem.exception.MemoryReadError, TypeError, ValueError, AttributeError) as e:
            logging.error(f"Exception during pointer resolution: {e}")
            return None

    def _aob_to_bytes(self, pattern: str) -> bytes:
        return bytes(int(b, 16) for b in re.findall(r"[0-9A-Fa-f]{2}", pattern))

    def _find_noclip_address(self, module) -> None:
        if not self.pm:
            return
        try:
            pattern_bytes = self._aob_to_bytes(config.NOCLIP_AOB_PATTERN)
            self.noclip_address = pymem.pattern.pattern_scan_module(self.pm.process_handle, module, pattern_bytes, return_multiple=False)
            if self.noclip_address:
                logging.info(f"[Bypass] Address found: {hex(self.noclip_address)}")
            else:
                logging.warning("[Bypass] Pattern not found.")
        except Exception as e:
            logging.error(f"[Bypass] Error scanning for pattern: {e}")
            self.noclip_address = None

    def is_moving(self, addresses: ResolvedAddresses) -> bool:
        """Check if the player has significant velocity in memory."""
        if not self.pm or not addresses:
            return False
        try:
            vx = abs(self.read_float(addresses.velocity_x) or 0.0)
            vy = abs(self.read_float(addresses.velocity_y) or 0.0)
            vz = abs(self.read_float(addresses.velocity_z) or 0.0)
            # Use a small threshold to account for floating point inaccuracies or slight drift
            threshold = 0.1
            return vx > threshold or vy > threshold or vz > threshold
        except Exception:
            return False  # Assume not moving if read fails

    def update_noclip_patch(self, should_be_moving: bool):
        if not self.pm or not self.noclip_address:
            return

        try:
            if should_be_moving and not self._is_noclip_patched:
                if self.write_bytes(self.noclip_address, config.PATCHED_NOCLIP_BYTES):
                    self._is_noclip_patched = True
            elif not should_be_moving and self._is_noclip_patched:
                if self.write_bytes(self.noclip_address, config.ORIGINAL_NOCLIP_BYTES):
                    self._is_noclip_patched = False
        except Exception as e:
            logging.error(f"[Bypass] Error updating patch status: {e}")
            # Disable bypass if patching fails critically
            self.noclip_address = None


# --- Static Utility Functions ---


def is_process_running(process_name: str) -> bool:
    for p in psutil.process_iter(["name"]):
        try:
            if p.info["name"] == process_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def wait_for_process(process_name: str, interval_s: float = 1.0):
    logging.info(f"Waiting for process {process_name}...")
    while not is_process_running(process_name):
        time.sleep(interval_s)
    logging.info(f"Process {process_name} found.")


def get_foreground_process_pid() -> Optional[int]:
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except (pywintypes.error, OSError, AttributeError):
        # AttributeError can happen if win32gui functions aren't available
        logging.warning("Could not get foreground window PID. win32gui might be missing or failed.")
        return None
