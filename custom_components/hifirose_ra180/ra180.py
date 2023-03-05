"""
Support for controlling a HifiRose RA180 over a network connection.

For more details about this platform, please refer to the documentation at
https://github.com/danieleva/hifirose_ra180
"""

import requests
from enum import Enum


class RA180States(Enum):
    @classmethod
    def from_value(cls, value):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f'Invalid value {value} for {cls.__name__} enumeration')

class Inputs(RA180States):
    LINE1,LINE2,LINE3,PHONO,BALANCE = range(1,6)

class VolumeStep(RA180States):
    DOWN,UP = range(0,2)

class Mute(RA180States):
    OFF,ON = range(0,2)

class PowerState(RA180States):
    OFF,ON = range(0,2)

class StandbyMode(RA180States):
    LOWPOWER,NORMAL = range(0,2)

class SoundModes(RA180States):
    OFF,A,B = range(0,3)

class Attenuator(RA180States):
    OFF,ON = range(0,2)

class Subsonic(RA180States):
    OFF,ON = range(0,2)

class PhonoAmp(RA180States):
    OFF,ON = range(0,2)

class PreAmp(RA180States):
    OFF,ON = range(0,2)

class CrossOver(RA180States):
    OFF,ON = range(0,2)



class RA180():

    READ_STATES = {
        "all": "/api/v1/all",
    }

    SET_STATES = {
        "volume": {"path": "/api/v1/volume", "parameter": "volume"},
        "volstep": {"path": "/api/v1/volstep", "parameter": "dir"},
        "mute": {"path": "/api/v1/mute", "parameter": "state"},
        "power": {"path": "/api/v1/power", "parameter": "state"},
        "standbymode": {"path":"/api/v1/power", "parameter": "mode"},
        "input": {"path": "/api/v1/input", "parameter": "input"},
        "apo": {"path": "/api/v1/apo", "parameter": "period"}
    }

    def __init__(self, device: str):
        self._device = device

    def _read_request(self, path: str) -> dict:
        response = requests.get("http://" + self._device + path)
        return response.json()

    def _set_request(self, path: str, value:dict) -> dict:
        response = requests.put(
            url="http://" + self._device + path,
            json=value,
        )
        return response.json()

    def _read_state(self, item: str) -> dict:
        """
        The state dump returned for "all" by the amplifier is:
        {
            "sdk_version": "v4.3.1",
            "chip_cores": 2,
            "chip_revision": 3,
            "fw_version": "v1.56",
            "main_mcu_version": 19,
            "front_mcu_version": 19,
            "ssid": "*****",
            "password": "*****",
            "rssi": -85,
            "addr": "192.168.1.168",
            "mac": "AA:BB:CC:DD:EE:FF",
            "powerstate": 1,
            "powermode": 0,
            "input": 5,
            "speaker": 1,
            "pure": 0,
            "preamp": 0,
            "tweeter": 0,
            "phono": 0,
            "phono_base": 4,
            "phono_treble": 2,
            "dimmer": 2,
            "subsonic": 0,
            "attenuator": 0,
            "mmmc": 0,
            "btl": 2,
            "volume": 5193,
            "vumode": 0,
            "vuboostdb": 0,
            "volmin": 28,
            "volmax": 60716,
            "volspeed": 15,
            "volmode": 0,
            "volfixed": 50,
            "mute": 0,
            "purelock": 1,
            "apoperiod": 1
        }
        ssid and password are sent in creatext in the response. You need to be on the same wifi network as the amplifier to get this, still I don't think the api is doing the right thing there.
        """
        return self._read_request(self.READ_STATES[item])

    def read_global_state(self) -> dict:
        return self._read_state("all")

    def formatted_state(self) -> dict:
        """
        Returns a dict in a format compatible with hass mediaplayer
        """
        state = self.read_global_state()
        power = PowerState.from_value(state["powerstate"])
        mute = Mute.from_value(state["mute"])
        source = Inputs.from_value(state["input"])
        soundmode = SoundModes.from_value(state["speaker"])
        standbymode = StandbyMode.from_value(state["powermode"])
        attenuator = Attenuator.from_value(state["attenuator"])
        subsonic = Subsonic.from_value(state["subsonic"])
        phono = PhonoAmp.from_value(state["phono"])
        preamp = PreAmp.from_value(state["preamp"])
        crossover = CrossOver.from_value(state["tweeter"]) 
        # Hass wants the volume value as float between 0 and 1
        normalised_volume = ((state["volume"]- state["volmin"]) / (state["volmax"]-state["volmin"]))

        return {
            "power": power.name,
            "source": source.name,
            "mute": mute.name,
            "soundmode": soundmode.name,
            "volume_level": normalised_volume,
            "standby_mode": standbymode,
            "attenuator": attenuator,
            "subsonic": subsonic,
            "phono": phono,
            "preamp": preamp,
            "crossover": crossover,
        }


    def _set_state(self, item: str, value: int) -> dict:
        key = self.SET_STATES[item]["parameter"]
        path = self.SET_STATES[item]["path"]
        payload = {
            key: value
        }
        return self._set_request(path, payload)

    def volume_step(self, step: VolumeStep)-> dict:
        return self._set_state("volstep", step.value)

    def increase_volume(self) -> dict:
        return self.volume_step(VolumeStep.UP)

    def decrease_volume(self) -> dict:
        return self.volume_step(VolumeStep.DOWN)

    def volume_set(self, value:int) -> dict:
        return self._set_state("volume", value)

    def volume_set_absolute(self, value:float) -> dict:
        """
        Expects a float value in the range 0..1. Converts it to ra180 value using min/max as reported by the amplifier
        """
        state = self.read_global_state()
        min = state["volmin"]
        max = state["volmax"]
        relative_volume = int(value * (max-min) + min)
        return self.volume_set(relative_volume)

    def input_set(self, input: Inputs) -> dict:
        return self._set_state("input", input.value)

    def toggle_mute(self, state: Mute) -> dict:
        return self._set_state("mute", state.value)

    def mute(self) -> dict:
        return self.toggle_mute(Mute.ON)

    def unmute(self) -> dict:
        return self.toggle_mute(Mute.OFF)
    
    def apo_set(self, hours:int) -> dict:
        return self._set_state("apo", hours)

    def toggle_power(self, state: PowerState) -> dict:
        return self._set_state("power", state.value)

    def power_on(self) -> dict:
        return self.toggle_power(PowerState.ON)

    def power_off(self) -> dict:
        return self.toggle_power(PowerState.OFF)

    def toggle_standby_mode(self, state: StandbyMode) -> dict:
        return self._set_state("standbymode", state.value)

    def normal_standby(self) -> dict:
        return self.toggle_standby_mode(StandbyMode.NORMAL)

    def low_power_standby(self) -> dict:
        return self.toggle_standby_mode(StandbyMode.LOWPOWER)



