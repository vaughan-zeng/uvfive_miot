"""Code to handle a Five MIoT Device."""
import logging

from miio import Device, DeviceException

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity

from .const import CONF_MAC, CONF_MODEL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConnectFiveDevice:
    """Class to async connect to a Five MIoT Device."""

    def __init__(self, hass):
        """Initialize the entity."""
        self._hass = hass
        self._device = None
        self._device_info = None

    @property
    def device(self):
        """Return the class containing all connections to the device."""
        return self._device

    @property
    def device_info(self):
        """Return the class containing device info."""
        return self._device_info

    async def async_connect_device(self, host, token):
        """Connect to the Five MIoT Device."""
        _LOGGER.debug("Initializing Five MIoT device with host %s (token %s...)", host, token[:5])
        try:
            self._device = Device(host, token)
            # get the device info
            self._device_info = await self._hass.async_add_executor_job(
                self._device.info
            )
        except DeviceException:
            _LOGGER.error(
                "DeviceException during setup of Five MIoT device with host %s", host
            )
            return False
        _LOGGER.debug(
            "%s %s %s detected",
            self._device_info.model,
            self._device_info.firmware_version,
            self._device_info.hardware_version,
        )
        return True


class FiveMIoTEntity(Entity):
    """Representation of a base Five MIoT Entity."""

    def __init__(self, name, device, entry, unique_id):
        """Initialize the Five MIoT Device."""
        self._device = device
        self._model = entry.data[CONF_MODEL]
        self._mac = entry.data[CONF_MAC]
        self._device_id = entry.unique_id
        self._unique_id = unique_id
        self._name = name

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of this entity, if any."""
        return self._name

    @property
    def device_info(self):
        """Return the device info."""
        device_info = {
            "identifiers": {(DOMAIN, self._device_id)},
            "manufacturer": "Five",
            "name": self._name,
            "model": self._model,
        }

        if self._mac is not None:
            device_info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._mac)}

        return device_info