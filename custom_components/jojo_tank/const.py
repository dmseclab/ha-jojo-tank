"""Constants for the JoJo Tank Monitor integration."""

DOMAIN = "jojo_tank"
PLATFORMS = ["sensor"]

CONF_TANK_NAME = "tank_name"
CONF_MQTT_TOPIC = "mqtt_topic"
CONF_TANK_CAPACITY = "tank_capacity"
CONF_TANK_HEIGHT = "tank_height"
CONF_EMPTY_CURRENT = "empty_current"
CONF_FULL_CURRENT = "full_current"
CONF_SENSE_RESISTOR = "sense_resistor"

DEFAULT_TANK_NAME = "JoJo Water Tank"
DEFAULT_MQTT_TOPIC = "homeassistant/sensor/jojo_tank/state"
DEFAULT_TANK_CAPACITY = 5250.0
DEFAULT_TANK_HEIGHT = 1850.0
DEFAULT_EMPTY_CURRENT = 4.0
DEFAULT_FULL_CURRENT = 11.5
DEFAULT_SENSE_RESISTOR = 120.0

DATA_LATEST = "latest"
DATA_UNSUB = "unsub"
SIGNAL_UPDATE = f"{DOMAIN}_update"
