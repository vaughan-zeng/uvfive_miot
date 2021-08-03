"""Config flow to configure uvFive MIoT device."""
import logging
from re import search

from miio import Device, DeviceException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
    CONF_DEVICE,
    CONF_MAC,
    ATTR_MODE
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.device_registry import format_mac


_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "uvFive MIoT device"
DOMAIN = "uvfive"

CONF_FLOW_TYPE = "config_flow_device"
CONF_MODEL = "model"
CONF_MODELS = [
    "uvfive.s_lamp.slmap2",
    "uvfive.steriliser.tiger",
]


DEVICE_CONFIG = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
    vol.Optional(CONF_NAME, default = DEFAULT_NAME): str,
    vol.Optional(CONF_MODEL, default = ''): vol.In(CONF_MODELS),
})


class uvFiveMiotFlowHandler(config_entries.ConfigFlow, domain = DOMAIN):
    """Handle a uvFive MIoT config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self.host = None
        self.mac = None

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        return await self.async_step_device()

    async def async_step_zeroconf(self, discovery_info):
        """Handle zeroconf discovery."""
        name = discovery_info.get("name")
        self.host = discovery_info.get("host")
        self.mac = discovery_info.get("properties", {}).get("mac")
        if self.mac is None:
            poch = discovery_info.get("properties", {}).get("poch", "")
            result = search(r"mac=\w+", poch)
            if result is not None:
                self.mac = result.group(0).split("=")[1]

        if not name or not self.host or not self.mac:
            return self.async_abort(reason="not_uvfive_miot")

        self.mac = format_mac(self.mac)

        # Check which device is discovered.
        for device_model in CONF_MODELS:
            if name.startswith(device_model.replace(".", "-")):
                unique_id = self.mac
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured({CONF_HOST: self.host})

                self.context.update(
                    {"title_placeholders": {"name": f"{device_model} {self.host}"}}
                )

                return await self.async_step_device()

        # Discovered device is not yet supported
        _LOGGER.debug(
            "Not yet supported uvFive MIoT device '%s' discovered with host %s",
            name,
            self.host,
        )
        return self.async_abort(reason="not_uvfive_miot")

    async def async_step_device(self, user_input=None):
        """Handle a flow initialized by the user to configure a uvfive miot device."""
        errors = {}
        if user_input is not None:
            self.host = user_input[CONF_HOST]
            token = user_input[CONF_TOKEN]
            name = user_input[CONF_NAME]
            if user_input.get(CONF_MODEL):
                model = user_input.get(CONF_MODEL)

            try:
                miot_device = Device(self.host, token)
                device_info = miot_device.info()
                # model = device_info.model

                _LOGGER.info(
                    "%s %s %s detected",
                    model,
                    device_info.firmware_version,
                    device_info.hardware_version,
                )
            except DeviceException as ex:
                raise PlatformNotReady from ex


            unique_id = f"{model}-{device_info.mac_address}-uvfive"

            if model is None and device_info is not None:
                model = device_info.model

            if model is not None:
                if self.mac is None and device_info is not None:
                    self.mac = format_mac(device_info.mac_address)

                # Setup uvFive MIoT device
                await self.async_set_unique_id(unique_id, raise_on_progress=False)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title = name,
                    data = {
                        CONF_FLOW_TYPE: CONF_DEVICE,
                        CONF_HOST: self.host,
                        CONF_TOKEN: token,
                        CONF_MODEL: model,
                        CONF_MAC: self.mac,
                    },
                )

        schema = DEVICE_CONFIG

        return self.async_show_form(step_id="device", data_schema=schema, errors=errors)
