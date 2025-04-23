# hacks.py
import keyboard
import math
from typing import Optional

import config
from memory import MemoryManager
from entities import ResolvedAddresses, MovementVector, CameraPerspective


def _get_camera_perspective(mem_manager: MemoryManager, addresses: ResolvedAddresses) -> Optional[CameraPerspective]:
    """Reads camera perspective values from memory."""
    if not addresses:
        return None
    x_per = mem_manager.read_float(addresses.camera_x)
    y_per = mem_manager.read_float(addresses.camera_y)
    z_per = mem_manager.read_float(addresses.camera_z)

    if x_per is None or y_per is None or z_per is None:
        return None
    return CameraPerspective(x=x_per, y=y_per, z=z_per)


def _calculate_horizontal_movement(cam_perspective: CameraPerspective, speed: float) -> MovementVector:
    """Calculates desired XZ movement based on camera and WASD keys."""
    move = MovementVector()

    hrz_magnitude_sq = cam_perspective.x * cam_perspective.x + cam_perspective.z * cam_perspective.z
    if hrz_magnitude_sq > 1e-9:  # Avoid division by zero or near-zero
        hrz_magnitude = math.sqrt(hrz_magnitude_sq)
        x_norm = cam_perspective.x / hrz_magnitude
        z_norm = cam_perspective.z / hrz_magnitude
    else:
        x_norm = 1.0
        z_norm = 0.0

    if keyboard.is_pressed("w"):
        move.x += x_norm
        move.z += z_norm
    if keyboard.is_pressed("s"):
        move.x -= x_norm
        move.z -= z_norm
    if keyboard.is_pressed("a"):
        move.x += z_norm
        move.z -= x_norm
    if keyboard.is_pressed("d"):
        move.x -= z_norm
        move.z += x_norm

    move_magnitude_sq = move.x * move.x + move.z * move.z
    if move_magnitude_sq > 1e-9:
        move_magnitude = math.sqrt(move_magnitude_sq)
        move.x = (move.x / move_magnitude) * speed
        move.z = (move.z / move_magnitude) * speed
    else:
        move.x = 0.0
        move.z = 0.0

    return move


def apply_accelboost(mem_manager: MemoryManager, addresses: ResolvedAddresses):
    cfg = config.app_config
    cam_perspective = _get_camera_perspective(mem_manager, addresses)
    if not cam_perspective:
        return

    movement = _calculate_horizontal_movement(cam_perspective, cfg.accel_boost_speed)

    if keyboard.is_pressed("space"):
        movement.y = cfg.jump_force
    elif keyboard.is_pressed("shift"):
        movement.y = config.ZERO_VERTICAL_VELOCITY

    mem_manager.write_float(addresses.velocity_x, movement.x)
    mem_manager.write_float(addresses.velocity_z, movement.z)
    if keyboard.is_pressed("space") or keyboard.is_pressed("shift"):
        mem_manager.write_float(addresses.velocity_y, movement.y)


def apply_fly(mem_manager: MemoryManager, addresses: ResolvedAddresses):
    cfg = config.app_config
    cam_perspective = _get_camera_perspective(mem_manager, addresses)
    if not cam_perspective:
        return

    movement = _calculate_horizontal_movement(cam_perspective, cfg.fly_speed)

    if keyboard.is_pressed("space"):
        movement.y = cfg.fly_speed
    elif keyboard.is_pressed("<"):
        movement.y = -cfg.fly_speed
    else:
        # Set Y velocity to near zero to counteract gravity when flying horizontally
        movement.y = config.ZERO_VERTICAL_VELOCITY

    mem_manager.write_float(addresses.velocity_x, movement.x)
    mem_manager.write_float(addresses.velocity_z, movement.z)
    mem_manager.write_float(addresses.velocity_y, movement.y)
