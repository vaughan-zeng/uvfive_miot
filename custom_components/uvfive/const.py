"""Constants for the Five MIoT device component."""
DOMAIN = "uvfive"

CONF_FLOW_TYPE = "config_flow_device"
CONF_DEVICE = "device"
CONF_MODEL = "model"
CONF_MAC = "mac"
SWITCH_PLATFORMS = ["switch"]
UVFIVE_MODELS = [
    "uvfive.s_lamp.slmap2",
    "uvfive.steriliser.tiger",
]
SERVICE_SET_CHILD_LOCK_ON = "set_child_lock_on"
SERVICE_SET_CHILD_LOCK_OFF = "set_child_lock_off"

SERVICE_SET_SLAMP_STERILIZATION_TIME = "set_slamp_sterilization_time"
SERVICE_SET_SLAMP_DISABLE_RADAR_ON = "set_slamp_disable_radar_on"
SERVICE_SET_SLAMP_DISABLE_RADAR_OFF = "set_slamp_disable_radar_off"

SERVICE_SET_RACK_TARGET_TIME = "set_rack_target_time"
SERVICE_SET_RACK_ALARM_ON = "set_rack_alarm_on"
SERVICE_SET_RACK_ALARM_OFF = "set_rack_alarm_off"
SERVICE_SET_RACK_RUNNING_MODE = 'set_rack_running_mode'