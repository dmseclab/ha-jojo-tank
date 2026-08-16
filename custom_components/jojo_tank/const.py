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
CONF_REFILL_THRESHOLD = "refill_threshold"
CONF_REFILL_TIMEOUT = "refill_timeout"

DEFAULT_TANK_NAME = "JoJo Water Tank"
DEFAULT_MQTT_TOPIC = "homeassistant/sensor/jojo_tank/state"
DEFAULT_TANK_CAPACITY = 5250.0
DEFAULT_TANK_HEIGHT = 1850.0
DEFAULT_EMPTY_CURRENT = 4.0
DEFAULT_FULL_CURRENT = 11.5
DEFAULT_SENSE_RESISTOR = 120.0
DEFAULT_REFILL_THRESHOLD = 75.0
DEFAULT_REFILL_TIMEOUT = 15.0

DATA_LATEST = "latest"
DATA_UNSUB = "unsub"
DATA_REFILLING = "refilling"
DATA_LAST_REFILL_AMOUNT = "last_refill_amount"
DATA_LAST_REFILL_TIME = "last_refill_time"
DATA_PREVIOUS_VOLUME = "previous_volume"
DATA_REFILL_TIMER = "refill_timer"
SIGNAL_UPDATE = f"{DOMAIN}_update"
