"""
Support for controlling a HifiRose RA180 over a network connection.

For more details about this platform, please refer to the documentation at
https://github.com/danieleva/hifirose_ra180
"""

import logging
from .ra180 import RA180, Inputs, Mute,SoundModes, PowerState
# import urllib.request
# import requests
import voluptuous as vol
# import socket
#from serial import Serial
import requests
from homeassistant.helpers.device_registry import format_mac

from homeassistant.components.media_player import MediaPlayerEntity ,MediaPlayerEntityFeature, PLATFORM_SCHEMA


from homeassistant.const import (
    CONF_DEVICE,
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
)

import homeassistant.helpers.config_validation as cv

import homeassistant.loader as loader

__version__ = "0.1"

_LOGGER = logging.getLogger(__name__)


SUPPORT_RA180 = (
    MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
)

DEFAULT_NAME = "HifiRose RA180"
DEVICE_CLASS = "receiver"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

def setup_platform(hass, config, add_devices, discovery_info=None):
    device = config.get(CONF_DEVICE)
    name = config.get(CONF_NAME)


    if device is None:
        _LOGGER.error("No host defined in configuration.yaml for HifiRose RA180")
        return


    add_devices([HifiRoseRA180Device(hass, device, name)])


class HifiRoseRA180Device(MediaPlayerEntity):
    def __init__(self, hass, device, name):
        _LOGGER.info("Setting up HifiRose RA180")
        self._hass = hass
        self._device = device

        self._name = name
        self._pwstate = ""
        self._state = STATE_OFF
        self._interface = RA180(device)
        
        
    def update(self):
        self._global_state = self._interface.formatted_state()
        self._pwstate = self._global_state["power"]
        self._mediasource = self._global_state["source"]
        self._muted = self._global_state["mute"]
        self._soundmode = self._global_state["soundmode"]
        self._volume_level = float(self._global_state["volume_level"])


    @property
    def is_volume_muted(self):
        if Mute.ON.name in self._muted:
            return True
        else:
            return False

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._mediasource

    @property
    def sound_mode(self):
        return self._soundmode

    @property
    def sound_mode_list(self):
        return sorted(list(SoundModes.__members__))

    @property
    def source_list(self):
        return sorted(list(Inputs.__members__))

    @property
    def state(self):
        if PowerState.ON.name in self._pwstate:
            return STATE_ON
        else:
            return STATE_OFF

    @property
    def supported_features(self):
        return SUPPORT_RA180

    def mute_volume(self, mute):
        if mute:
            self._interface.mute()
        else:
            self._interface.unmute()

    def select_source(self, source):
        self._interface.input_set(getattr(Inputs, source))

    def turn_on(self):
        self._interface.power_on()

    def turn_off(self):
        self._interface.power_off()

    @property
    def volume_level(self):
        return self._volume_level

    def volume_up(self):
        self._interface.increase_volume()

    def volume_down(self):
        self._interface.decrease_volume()
    
    def set_volume_level(self, volume:float) -> None:
        self._interface.volume_set_absolute(volume)
        