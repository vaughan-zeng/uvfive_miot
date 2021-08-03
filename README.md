# *** Beta



# uvFive MIoT device

This is a custom component for Home Assistant to integrate the uvFive MIoT device.

Please follow the instructions on [Retrieving the Access Token](https://home-assistant.io/components/xiaomi/#retrieving-the-access-token) to get the API token to use in the configuration.yaml file.

Credits: Thanks to [Rytilahti](https://github.com/rytilahti/python-miio) for all the work.

## Features

### uvFive Sterilization Lamp

Supported models: `uvfive.s_lamp.slmap2`.

* Power (on, off)
* Child Lock (on, off)
* Disable Radar (on, off)
* Setting Sterilization Time (5...45 minutes)
* Attributes
  - Stop Countdown
  - Child Lock
  - Fault Info
  - Status
  - Model
  - Sterilization Time
  - Disable Radar

### uvFive Sterilization Rack

Supported models: `uvfive.steriliser.tiger`.

* Power (on, off)
* Child Lock (on, off)
* Disable Radar (on, off)
* Setting Rack Target Time (15...90 minutes)
* Alarm (on, off)
* Running Mode (Normal, Quick, Favourite)
* Attributes
  - Stop Countdown
  - Child Lock
  - Fault Info
  - Status
  - Model
  - Mode
  - Target Time
  - Working Time
  - Alarm

# Install
Download and copy custom_components/uvfive folder to custom_components folder in your HomeAssistant config folder

Or you can install component with HACS

# Config

## HomeAssistant GUI
Configuration > Integration > + > uvfive

### Configuration variables:
- **name** (*Optional*): The name of your uvFive MIoT device.
- **host** (*Required*): The IP of your uvFive MIoT device.
- **token** (*Required*): The API token of your uvFive MIoT device.
- **mode** (*Optional*): The mode of your uvFive MIoT device.


# Platform services

#### Service `uvfive.set_child_lock__on`

Turn the child lock on.

| Service data attribute | Optional | Description                            |
| ---------------------- | -------- | -------------------------------------- |
| `entity_id`            | no       | Name of the uvFive MIoT device entity. |

#### Service `uvfive.set_child_lock__off`

Turn the child lock off.

| Service data attribute | Optional | Description                            |
| ---------------------- | -------- | -------------------------------------- |
| `entity_id`            | no       | Name of the uvFive MIoT device entity. |

#### Service `uvfive.set_slamp_disable_radar_on`

Turn the uvFive sterilization lamp disable radar on.

| Service data attribute | Optional | Description                                   |
| ---------------------- | -------- | --------------------------------------------- |
| `entity_id`            | no       | Name of the uvFive sterilization lamp entity. |

#### Service `uvfive.set_slamp_disable_radar_off`

Turn the uvFive sterilization lamp disable radar off.

| Service data attribute | Optional | Description                                   |
| ---------------------- | -------- | --------------------------------------------- |
| `entity_id`            | no       | Name of the uvFive sterilization lamp entity. |

#### Service `uvfive.set_slamp_sterilization_time`

Set the uvFive sterilization lamp sterilization time.

| Service data attribute | Optional | Description                                   |
| ---------------------- | -------- | --------------------------------------------- |
| `entity_id`            | no       | Name of the uvFive sterilization lamp entity. |
| `minutes`              | no       | Sterilization time, between 5 and 45.         |

#### Service `uvfive.set_rack_target_time`

Set the uvfive sterilization rack target time.

| Service data attribute | Optional | Description                                   |
| ---------------------- | -------- | --------------------------------------------- |
| `entity_id`            | no       | Name of the uvfive sterilization rack entity. |
| `minutes`              | no       | Target time, between 15 and 90.               |

#### Service `uvfive.set_rack_alarm_on`

Turn the uvfive sterilization rack alarm on.

| Service data attribute | Optional | Description                                   |
| ---------------------- | -------- | --------------------------------------------- |
| `entity_id`            | no       | Name of the uvfive sterilization rack entity. |

#### Service `uvfive.set_rack_alarm_off`

Turn the uvfive sterilization rack alarm off.

| Service data attribute | Optional | Description                                   |
| ---------------------- | -------- | --------------------------------------------- |
| `entity_id`            | no       | Name of the uvfive sterilization rack entity. |

#### Service `uvfive.set_rack_running_mode`

Set the uvfive sterilization rack running mode.

| Service data attribute | Optional | Description                                                  |
| ---------------------- | -------- | ------------------------------------------------------------ |
| `entity_id`            | no       | Name of the uvfive sterilization rack entity.                |
| `mode`                 | no       | Running mode, valid values are 'Normal', 'Quick' and 'Favourite'. |