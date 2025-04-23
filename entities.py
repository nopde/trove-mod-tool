# entities.py
from dataclasses import dataclass


@dataclass
class ResolvedAddresses:
    velocity_x: int = 0
    velocity_y: int = 0
    velocity_z: int = 0
    camera_x: int = 0
    camera_y: int = 0
    camera_z: int = 0


@dataclass
class MovementVector:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class CameraPerspective:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
