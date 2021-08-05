"""Support for Five MIoT device."""
from datetime import timedelta
import logging

from homeassistant import config_entries, core

from .const import (
    CONF_MODEL,
    DOMAIN,
    SWITCH_PLATFORMS,
    UVFIVE_MODELS,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    """Set up the Xiaomi Miio components from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    return bool(
        await async_setup_device_entry(hass, entry)
    )


async def async_setup_device_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    """Set up the Xiaomi Miio device component from a config entry."""
    model = entry.data[CONF_MODEL]

    # Identify platforms to setup
    platforms = []

    if model in UVFIVE_MODELS:
        platforms = SWITCH_PLATFORMS

    if not platforms:
        return False

    for platform in platforms:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, platform))

    return True

