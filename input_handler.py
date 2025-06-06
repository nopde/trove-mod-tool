# input_handler.py
import keyboard
import config
import logging


def toggle_hack():
    config.app_config.hack_on = not config.app_config.hack_on
    status = "ON" if config.app_config.hack_on else "OFF"
    logging.info(f"Hack toggled to {status}")


def change_mode():
    cfg = config.app_config
    if cfg.current_hack == config.HackMode.ACCELBOOST:
        cfg.current_hack = config.HackMode.FLY
    elif cfg.current_hack == config.HackMode.FLY:
        cfg.current_hack = config.HackMode.ACCELBOOST
    else:
        cfg.current_hack = config.HackMode.ACCELBOOST

    logging.info(f"Hack mode changed to {cfg.current_hack.name}")


def increase_speed():
    cfg = config.app_config
    if cfg.current_hack == config.HackMode.ACCELBOOST:
        cfg.accel_boost_speed += 5.0
        logging.info(f"AccelBoost speed increased to {cfg.accel_boost_speed:.1f}")
    elif cfg.current_hack == config.HackMode.FLY:
        cfg.fly_speed += 5.0
        logging.info(f"Fly speed increased to {cfg.fly_speed:.1f}")


def decrease_speed():
    cfg = config.app_config
    # Prevent speeds from going below a reasonable minimum (e.g., 0 or 5)
    min_speed = 5.0
    if cfg.current_hack == config.HackMode.ACCELBOOST:
        cfg.accel_boost_speed = max(min_speed, cfg.accel_boost_speed - 5.0)
        logging.info(f"AccelBoost speed decreased to {cfg.accel_boost_speed:.1f}")
    elif cfg.current_hack == config.HackMode.FLY:
        cfg.fly_speed = max(min_speed, cfg.fly_speed - 5.0)
        logging.info(f"Fly speed decreased to {cfg.fly_speed:.1f}")


def setup_hotkeys():
    keyboard.add_hotkey("F3", toggle_hack)
    keyboard.add_hotkey("F4", change_mode)
    keyboard.add_hotkey("page up", increase_speed)
    keyboard.add_hotkey("page down", decrease_speed)


def remove_hotkeys():
    try:
        keyboard.remove_hotkey("F3")
        keyboard.remove_hotkey("F4")
        keyboard.remove_hotkey("page up")
        keyboard.remove_hotkey("page down")
        logging.info("Hotkeys removed.")
    except KeyError:
        # This can happen if hotkeys were somehow not registered
        logging.warning("Could not remove all hotkeys (might have been cleared already).")
    except Exception as e:
        logging.error(f"Error removing hotkeys: {e}")
