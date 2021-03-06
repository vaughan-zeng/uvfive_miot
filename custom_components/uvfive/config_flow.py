"""Config flow to configure Five MIoT device."""
import logging
from re import search

from miio import Device, DeviceException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.helpers.device_registry import format_mac
from homeassistant.exceptions import PlatformNotReady

from .const import (
    CONF_DEVICE,
    CONF_FLOW_TYPE,
    CONF_MAC,
    CONF_MODEL,
    DOMAIN,
    UVFIVE_MODELS,
)
from .device import ConnectFiveDevice

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Five MIoT device"
DEFAULT_LAMP_NAME = 'Five Sterilization Lamp'
DEFAULT_RACK_NAME = 'Five Sterilization Rack'

DEVICE_CONFIG = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
    # vol.Optional(CONF_NAME, default = DEFAULT_NAME): str,
    vol.Optional(CONF_NAME): str,
    # vol.Optional(CONF_MODEL, default = ''): vol.In(UVFIVE_MODELS),
})


class uvFiveMiotFlowHandler(config_entries.ConfigFlow, domain = DOMAIN):
    """Handle a Five MIoT config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self.host = None
        self.mac = None

    async def async_step_import(self, conf: dict):
        """Import a configuration from config.yaml."""
        host = conf[CONF_HOST]
        self.context.update({"title_placeholders": {"name": f"YAML import {host}"}})
        return await self.async_step_device(user_input=conf)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        return await self.async_step_device()

    async def async_step_zeroconf(self, discovery_info):
        """Handle zeroconf discovery."""
        _LOGGER.info("discovery_info: %s", discovery_info)
        name = discovery_info.get("name")
        _LOGGER.info("name: %s", name)
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
        for device_model in UVFIVE_MODELS:
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
            "Not yet supported Five MIoT device '%s' discovered with host %s",
            name,
            self.host,
        )
        return self.async_abort(reason="not_uvfive_miot")

    async def async_step_device(self, user_input=None):
        """Handle a flow initialized by the user to configure a Five MIoT device."""
        errors = {}
        if user_input is not None:
            self.host = user_input[CONF_HOST]
            token = user_input[CONF_TOKEN]
            if user_input.get(CONF_MODEL):
                model = user_input.get(CONF_MODEL)
            else:
                model = None

            # Try to connect to a Five MIoT Device.
            connect_device_class = ConnectFiveDevice(self.hass)
            await connect_device_class.async_connect_device(self.host, token)
            device_info = connect_device_class.device_info

            if model is None and device_info is not None:
                model = device_info.model

            if model is not None:
                if self.mac is None and device_info is not None:
                    self.mac = format_mac(device_info.mac_address)

                # Setup Five MIoT device
                if user_input.get(CONF_NAME):
                    name = user_input.get(CONF_NAME)
                else:
                    if model == 'uvfive.s_lamp.slmap2':
                        name = DEFAULT_LAMP_NAME
                    elif model == 'uvfive.steriliser.tiger':
                        name = DEFAULT_RACK_NAME
                    else:
                        name = DEFAULT_NAME

                for device_model in UVFIVE_MODELS:
                    if model.startswith(device_model):
                        unique_id = f"{model}-{device_info.mac_address}"

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

                errors["base"] = "unknown_device"
            else:
                errors["base"] = "cannot_connect"

        schema = DEVICE_CONFIG

        return self.async_show_form(step_id="device", data_schema=schema, errors=errors)
