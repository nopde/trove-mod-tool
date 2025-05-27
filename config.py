# config.py
from dataclasses import dataclass
from enum import Enum, auto

# --- Core Constants ---
PROCESS_NAME = "Trove.exe"
INTERVAL_MS = 10
ZERO_VERTICAL_VELOCITY = 0.305

# --- Memory Constants ---
LOCALPLAYER_AOB_PATTERN = "A1 ?? ?? ?? ?? 8B 40 ?? 85 C0 74 ?? 0F 28 ?? ?? EB 07 0F 28 05 ?? ?? ?? ?? 80"
NOCLIP_AOB_PATTERN = "DC 67 68"
ORIGINAL_NOCLIP_BYTES = b"\xdc\x67"
PATCHED_NOCLIP_BYTES = b"\xdc\x47"
POINTER_RESOLVE_INTERVAL_S = 0.1
VELOCITY_OFFSETS = [0x8, 0x28, 0xC4, 0x4]
CAMERA_OFFSETS = [0x4, 0x24, 0x84, 0x0]


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


app_config: Configuration = None  # Global app config, set in main.py
