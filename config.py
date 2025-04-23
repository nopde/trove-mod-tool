# config.py
from dataclasses import dataclass
from enum import Enum, auto

# --- Core Constants ---
PROCESS_NAME = "Trove.exe"
INTERVAL_MS = 10
ZERO_VERTICAL_VELOCITY = 0.305

# --- Memory Constants ---
STATIC_POINTER_START_OFFSET = 0x1098418
NOCLIP_AOB_PATTERN = "DC 67 68"
ORIGINAL_NOCLIP_BYTES = b"\xdc\x67"
PATCHED_NOCLIP_BYTES = b"\xdc\x47"
POINTER_RESOLVE_INTERVAL_S = 0.1


# --- Hack Modes Enum ---
class HackMode(Enum):
    ACCELBOOST = auto()
    FLY = auto()


# --- Mutable Configuration State ---
@dataclass
class Configuration:
    hack_on: bool = True
    current_hack: HackMode = HackMode.ACCELBOOST
    accel_boost_speed: float = 40.0
    fly_speed: float = 15.0
    jump_force: float = 25.0


# --- Global Config Instance ---
app_config = Configuration()
