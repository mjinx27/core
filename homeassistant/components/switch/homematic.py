"""
The homematic switch platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.homematic/

Important: For this platform to work the homematic component has to be
properly configured.

Configuration:

switch:
  - platform: homematic
    address: <Homematic address for device> # e.g. "JEQ0XXXXXXX"
    name: <User defined name> (optional)
    button: n (integer of channel to map, device-dependent) (optional)
"""

import logging
from homeassistant.components.switch import SwitchDevice
from homeassistant.const import STATE_UNKNOWN
import homeassistant.components.homematic as homematic

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['homematic']


def setup_platform(hass, config, add_callback_devices, discovery_info=None):
    """Setup the platform."""
    if discovery_info:
        config = discovery_info
    return homematic.setup_hmdevice_entity_helper(HMSwitch,
                                                  config,
                                                  add_callback_devices)


class HMSwitch(homematic.HMDevice, SwitchDevice):
    """Represents a Homematic Switch in Home Assistant."""

    @property
    def is_on(self):
        """Return True if switch is on."""
        try:
            return self._hm_get_state() > 0
        except TypeError:
            return False

    @property
    def current_power_mwh(self):
        """Return the current power usage in mWh."""
        if "ENERGY_COUNTER" in self._data:
            try:
                return self._data["ENERGY_COUNTER"] / 1000
            except ZeroDivisionError:
                return 0

        return None

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        if self.available:
            self._hmdevice.on(self._channel)

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        if self.available:
            self._hmdevice.off(self._channel)

    def _check_hm_to_ha_object(self):
        """Check if possible to use the HM Object as this HA type."""
        from pyhomematic.devicetypes.actors import Dimmer, Switch

        # Check compatibility from HMDevice
        if not super()._check_hm_to_ha_object():
            return False

        # Check if the homematic device is correct for this HA device
        if isinstance(self._hmdevice, Switch):
            return True
        if isinstance(self._hmdevice, Dimmer):
            return True

        _LOGGER.critical("This %s can't be use as switch!", self._name)
        return False

    def _init_data_struct(self):
        """Generate a data dict (self._data) from hm metadata."""
        from pyhomematic.devicetypes.actors import Dimmer,\
            Switch, SwitchPowermeter

        super()._init_data_struct()

        # Use STATE
        if isinstance(self._hmdevice, Switch):
            self._state = "STATE"

        # Use LEVEL
        if isinstance(self._hmdevice, Dimmer):
            self._state = "LEVEL"

        # Need sensor values for SwitchPowermeter
        if isinstance(self._hmdevice, SwitchPowermeter):
            for node in self._hmdevice.SENSORNODE:
                self._data.update({node: STATE_UNKNOWN})

        # Add state to data dict
        if self._state:
            _LOGGER.debug("%s init data dict with main node '%s'", self._name,
                          self._state)
            self._data.update({self._state: STATE_UNKNOWN})
        else:
            _LOGGER.critical("Can't correctly init light %s.", self._name)
