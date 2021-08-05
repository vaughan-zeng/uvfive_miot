"""Support for Five MIoT device."""
import asyncio
from functools import partial
import logging

from miio import Device, DeviceException
import voluptuous as vol
from enum import IntEnum
from datetime import datetime, timedelta

from homeassistant.components.switch import (
    # PLATFORM_SCHEMA,
    SwitchEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
)
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DEVICE,
    CONF_FLOW_TYPE,
    CONF_MAC,
    CONF_MODEL,
    DOMAIN,
    # UVFIVE_MODELS,
    SERVICE_SET_CHILD_LOCK_ON,
    SERVICE_SET_CHILD_LOCK_OFF,
    SERVICE_SET_SLAMP_STERILIZATION_TIME,
    SERVICE_SET_SLAMP_DISABLE_RADAR_ON,
    SERVICE_SET_SLAMP_DISABLE_RADAR_OFF,
    SERVICE_SET_RACK_TARGET_TIME,
    SERVICE_SET_RACK_ALARM_ON,
    SERVICE_SET_RACK_ALARM_OFF,
    SERVICE_SET_RACK_RUNNING_MODE,
)
from .device import FiveMIoTEntity

_LOGGER = logging.getLogger(__name__)

# DEFAULT_NAME = "Five MIoT device"
DATA_KEY = "switch.uvfive_miot"

# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
#     {
#         vol.Required(CONF_HOST): cv.string,
#         vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
#         vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
#         vol.Optional(CONF_MODEL): vol.In(UVFIVE_MODELS),
#     }
# )

ATTR_MINUTES = 'minutes'
ATTR_FAULT = 'fault_info'
ATTR_UV_STATUS = 'status'
ATTR_STOP_COUNTDOWN = 'stop_countdown'
ATTR_CHILD_LOCK = 'child_lock'
ATTR_MODEL = "model"

ATTR_SLAMP_STERILIZATION_TIME = 'sterilization_time'
ATTR_SLAMP_DISABLE_RADAR = 'Disable_radar'

ATTR_RACK_TARGET_TIME = 'target_time'
ATTR_RACK_WORKING_TIME = 'working_time'
ATTR_RACK_ALARM = 'alarm'

SUCCESS = ["ok"]

class sLampStatus(IntEnum):
    Idle = 1
    Standby = 2
    Running = 3
    Sterilizing = 4

class sLampFault(IntEnum):
    NoFault = 0
    CanNotRun = 1
    Invade = 2
    InvadeJam = 3
    TubeBroken = 4


class RackStatus(IntEnum):
    Idle = 0
    Fan = 1
    Dry = 2
    DryFan = 3
    Ste = 4
    SteFan = 5
    SteDry = 6
    SteDryFan = 7

class RackFault(IntEnum):
    NoFault = 0
    Complete = 1
    Abandon = 2

class RackMode(IntEnum):
    Normal = 0
    Quick = 1
    Favourite = 2


SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_SLAMP_STERILIZATION_TIME = SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_MINUTES): vol.All(int, vol.Range(min=5, max=45))}
)

SERVICE_SCHEMA_RACK_TARGET_TIME = SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_MINUTES): vol.All(int, vol.Range(min=15, max=90))}
)

SERVICE_SCHEMA_RACK_RUNNING_MODE = SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_MODE): vol.All(vol.In(['Normal', 'Quick', 'Favourite']))}
)

SERVICE_TO_METHOD = {
    SERVICE_SET_CHILD_LOCK_ON: {'method': "async_set_child_lock_on"},
    SERVICE_SET_CHILD_LOCK_OFF: {'method': "async_set_child_lock_off"},

    SERVICE_SET_SLAMP_STERILIZATION_TIME: {'method': 'async_set_slamp_sterilization_time',
        'schema': SERVICE_SCHEMA_SLAMP_STERILIZATION_TIME,},
    SERVICE_SET_SLAMP_DISABLE_RADAR_ON: {'method': "async_set_slamp_disable_radar_on"},
    SERVICE_SET_SLAMP_DISABLE_RADAR_OFF: {'method': "async_set_slamp_disable_radar_off"},

    SERVICE_SET_RACK_TARGET_TIME: {'method': 'async_set_rack_target_time',
        'schema': SERVICE_SCHEMA_RACK_TARGET_TIME,},
    SERVICE_SET_RACK_RUNNING_MODE: {'method': 'async_set_rack_running_mode',
        'schema': SERVICE_SCHEMA_RACK_RUNNING_MODE,},
    SERVICE_SET_RACK_ALARM_ON: {'method': "async_set_rack_alarm_on"},
    SERVICE_SET_RACK_ALARM_OFF: {'method': "async_set_rack_alarm_off"},
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Import Five MIoT device configuration from YAML."""
    _LOGGER.warning(
        "Loading Five MIoT device via platform setup is deprecated; Please remove it from your configuration"
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Five MIoT switch from a config entry."""
    entities = []

    host = config_entry.data[CONF_HOST]
    token = config_entry.data[CONF_TOKEN]
    name = config_entry.title
    model = config_entry.data[CONF_MODEL]
    unique_id = config_entry.unique_id

    if config_entry.data[CONF_FLOW_TYPE] == CONF_DEVICE:
        if DATA_KEY not in hass.data:
            hass.data[DATA_KEY] = {}

        _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])

        if model in ["uvfive.s_lamp.slmap2"]:
            uvfive_device = Device(host, token)
            device = FiveSterilizationLampSwitch(name, uvfive_device, config_entry, unique_id)
            entities.append(device)
            hass.data[DATA_KEY][host] = device
        elif model in ["uvfive.steriliser.tiger"]:
            uvfive_device = Device(host, token)
            device = FiveSterilizationRackSwitch(name, uvfive_device, config_entry, unique_id)
            entities.append(device)
            hass.data[DATA_KEY][host] = device
        else:
            _LOGGER.error(
                "Unsupported device found! Please create an issue at "
                "https://github.com/vaughan-zeng/uvfive_miot/issues "
                "and provide the following data: %s",
                model,
            )

        async def async_service_handler(service):
            """Map services to methods on Five MIoT device."""
            method = SERVICE_TO_METHOD.get(service.service)
            params = {
                key: value
                for key, value in service.data.items()
                if key != ATTR_ENTITY_ID
            }
            entity_ids = service.data.get(ATTR_ENTITY_ID)
            if entity_ids:
                devices = [
                    device
                    for device in hass.data[DATA_KEY].values()
                    if device.entity_id in entity_ids
                ]
            else:
                devices = hass.data[DATA_KEY].values()

            update_tasks = []
            for device in devices:
                if not hasattr(device, method["method"]):
                    continue
                await getattr(device, method["method"])(**params)
                update_tasks.append(device.async_update_ha_state(True))

            if update_tasks:
                await asyncio.wait(update_tasks)

        for uvfive_service in SERVICE_TO_METHOD:
            schema = SERVICE_TO_METHOD[uvfive_service].get("schema", SERVICE_SCHEMA)
            hass.services.async_register(
                DOMAIN, uvfive_service, async_service_handler, schema=schema
            )

    async_add_entities(entities, update_before_add=True)


class FiveMiotGenericSwitch(FiveMIoTEntity, SwitchEntity):
    """Representation of Five MIoT Switch Generic."""

    def __init__(self, name, device, entry, unique_id):
        """Initialize the Five MIoT Switch."""
        super().__init__(name, device, entry, unique_id)

        self._available = False
        self._state = None
        self._state_attrs = {
            ATTR_STOP_COUNTDOWN: None,
            ATTR_CHILD_LOCK: None,
            ATTR_FAULT: None,
            ATTR_UV_STATUS: None,
            ATTR_MODEL: self._model}
        self._skip_update = False

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a device command handling error messages."""
        try:
            result = await self.hass.async_add_executor_job(partial(func, *args, **kwargs))
            _LOGGER.debug("Response received from Five MIoT device: %s", result)
            return result == SUCCESS
        except DeviceException as exc:
            if self._available:
                _LOGGER.error(mask_error, exc)
                self._available = False
            return False

    async def _uvfive_turn_on(self, **kwargs):
        """Turn the Five MIoT Switch on."""
        result = await self._try_command(kwargs['error_info'], self._device.send,
            'set_properties', [{"siid":kwargs['siid'], "piid":kwargs['piid'], "value":True}]
        )

        if result:
            self._state = True
            self._skip_update = True

    async def _uvfive_turn_off(self, **kwargs):
        """Turn the Five MIoT Switch off."""
        result = await self._try_command(kwargs['error_info'], self._device.send,
            'set_properties', [{"siid":kwargs['siid'], "piid":kwargs['piid'], "value":False}]
        )

        if result:
            self._state = False
            self._skip_update = True

    async def _uvfive_set_child_lock(self, **kwargs):
        """Turn the child lock on."""
        await self._try_command(kwargs['error_info'], self._device.send,
            'set_properties', [{"siid":kwargs['siid'], "piid":kwargs['piid'], "value":kwargs['value']}]
        )


class FiveSterilizationLampSwitch(FiveMiotGenericSwitch):
    """Representation of Five Sterilization Lamp."""

    def __init__(self, name, uvfive_device, entry, unique_id):
        """Initialize the Five Sterilization Lamp."""
        super().__init__(name, uvfive_device, entry, unique_id)

        self._icon = 'mdi:lightbulb-cfl'
        self._state_attrs[ATTR_SLAMP_STERILIZATION_TIME] = None
        self._state_attrs[ATTR_SLAMP_DISABLE_RADAR] = None

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    async def async_turn_on(self):
        """Turn the Five Sterilization Lamp on."""
        await self._uvfive_turn_on(error_info = "Turning the Five Sterilization Lamp on failed.", 
            siid = 2, piid = 2,
        )

    async def async_turn_off(self):
        """Turn the Five Sterilization Lamp off."""
        await self._uvfive_turn_off(error_info = "Turning the Five Sterilization Lamp off failed.", 
            siid = 2, piid = 2,
        )

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(
                self._device.send,
                'get_properties',
                [{"siid":2,"piid":1},
                {"siid":2,"piid":2},
                {"siid":2,"piid":3},
                {"siid":2,"piid":6},
                {"siid":2,"piid":7},
                {"siid":4,"piid":1},
                {"siid":5,"piid":1}]
            )
            _LOGGER.debug("Got the Five Sterilization Lamp new state: %s", state)

            self._available = True

            self._state = state[1]['value']
            self._state_attrs[ATTR_FAULT] = sLampFault(state[0]['value']).name
            self._state_attrs[ATTR_UV_STATUS] = sLampStatus(state[2]['value']).name
            self._state_attrs[ATTR_SLAMP_STERILIZATION_TIME] = state[3]['value']
            self._state_attrs[ATTR_STOP_COUNTDOWN] = str(timedelta(seconds=state[4]['value']))
            self._state_attrs[ATTR_CHILD_LOCK] = state[5]['value']
            self._state_attrs[ATTR_SLAMP_DISABLE_RADAR] = state[6]['value']

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    async def async_set_slamp_sterilization_time(self, minutes: int):
        """Set the UV sterilization time."""
        await self._try_command("Setting the UV sterilization time failed.",
            self._device.send, 'set_properties', [{"siid":2,"piid":6,"value":minutes}]
        )

    async def async_set_child_lock_on(self):
        """Turn the child lock on."""
        await self._uvfive_set_child_lock(error_info = "Turning the child lock on failed.", 
            siid = 4, piid = 1, value = True,
        )

    async def async_set_child_lock_off(self):
        """Turn the child lock off."""
        await self._uvfive_set_child_lock(error_info = "Turning the child lock on failed.", 
            siid = 4, piid = 1, value = False,
        )

    async def async_set_slamp_disable_radar_on(self):
        """Turn the disable radar on."""
        await self._try_command( "Turning the disable radar on failed.",
            self._device.send, 'set_properties', [{"siid":5,"piid":1,"value":True}]
        )

    async def async_set_slamp_disable_radar_off(self):
        """Turn the disable radar off."""
        await self._try_command( "Turning the disable radar off failed.",
            self._device.send, 'set_properties', [{"siid":5,"piid":1,"value":False}]
        )


class FiveSterilizationRackSwitch(FiveMiotGenericSwitch):
    """Representation of Five Sterilization Rack."""

    def __init__(self, name, uvfive_device, entry, unique_id):
        """Initialize the Five Sterilization Rack."""
        super().__init__(name, uvfive_device, entry, unique_id)

        self._icon = 'mdi:toaster'
        self._state_attrs[ATTR_MODE] = None
        self._state_attrs[ATTR_RACK_TARGET_TIME] = None
        self._state_attrs[ATTR_RACK_WORKING_TIME] = None
        self._state_attrs[ATTR_RACK_ALARM] = None

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    async def async_turn_on(self):
        """Turn the Five Sterilization Rack on."""
        await self._uvfive_turn_on(error_info = "Turning the Five Sterilization Rack on failed.", 
            siid = 2, piid = 3,
        )

    async def async_turn_off(self):
        """Turn the Five Sterilization Rack off."""
        await self._uvfive_turn_off(error_info = "Turning the Five Sterilization Rack off failed.", 
            siid = 2, piid = 3,
        )


    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(
                self._device.send,
                'get_properties',
                [{"siid":2,"piid":1},
                {"siid":2,"piid":2},
                {"siid":2,"piid":3},
                {"siid":2,"piid":4},
                {"siid":2,"piid":5},
                {"siid":2,"piid":6},
                {"siid":2,"piid":7},
                {"siid":3,"piid":1},
                {"siid":4,"piid":1}]
            )
            _LOGGER.debug("Got the Five Sterilization Rack new state: %s", state)

            self._available = True

            self._state = state[2]['value']
            self._state_attrs[ATTR_FAULT] = RackFault(state[0]['value']).name
            self._state_attrs[ATTR_MODE] = RackMode(state[1]['value']).name
            self._state_attrs[ATTR_UV_STATUS] = RackStatus(state[3]['value']).name
            self._state_attrs[ATTR_RACK_TARGET_TIME] = str(timedelta(minutes=state[4]['value']))
            self._state_attrs[ATTR_RACK_WORKING_TIME] = str(timedelta(minutes=state[5]['value']))
            self._state_attrs[ATTR_STOP_COUNTDOWN] = str(timedelta(minutes=state[6]['value']))
            self._state_attrs[ATTR_RACK_ALARM] = state[7]['value']
            self._state_attrs[ATTR_CHILD_LOCK] = state[8]['value']

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    async def async_set_rack_running_mode(self, mode: str):
        """Set the Five Sterilization Rack running mode."""
        await self._try_command("Setting the Five Sterilization Rack running mode failed.",
            self._device.send, 'set_properties', [{"siid":2, "piid":2, "value":RackMode[mode].value}]
        )

    async def async_set_rack_target_time(self, minutes: int):
        """Set the Five Sterilization Rack target time."""
        await self._try_command("Setting the Five Sterilization Rack target time failed.",
            self._device.send, 'set_properties', [{"siid":2, "piid":5, "value":minutes}]
        )

    async def async_set_rack_alarm_on(self):
        """Turn the Five Sterilization Rack alarm on."""
        await self._try_command("Turning the Five Sterilization Rack alarm on failed.",
            self._device.send, 'set_properties', [{"siid":3, "piid":1, "value":True}]
        )

    async def async_set_rack_alarm_off(self):
        """Turn the Five Sterilization Rack alarm off."""
        await self._try_command("Turning the Five Sterilization Rack alarm off failed.",
            self._device.send, 'set_properties', [{"siid":3, "piid":1, "value":False}]
        )

    async def async_set_child_lock_on(self):
        """Turn the Five Sterilization Rack child lock on."""
        await self._uvfive_set_child_lock(error_info = "Turning the Five Sterilization Rack child lock on failed.", 
            siid = 4, piid = 1, value = True,
        )

    async def async_set_child_lock_off(self):
        """Turn the Five Sterilization Rack child lock off."""
        await self._uvfive_set_child_lock(error_info = "Turning the Five Sterilization Rack child lock off failed.", 
            siid = 4, piid = 1, value = False,
        )

