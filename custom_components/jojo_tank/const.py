"""Constants for the JoJo Tank Monitor integration."""

DOMAIN = "jojo_tank"
PLATFORMS = ["sensor", "binary_sensor"]

CONF_TANK_NAME = "tank_name"
CONF_MQTT_TOPIC = "mqtt_topic"
CONF_TANK_CAPACITY = "tank_capacity"
CONF_TANK_HEIGHT = "tank_height"
CONF_EMPTY_CURRENT = "empty_current"
CONF_FULL_CURRENT = "full_current"
CONF_SENSE_RESISTOR = "sense_resistor"
CONF_REFILL_THRESHOLD = "refill_threshold"
CONF_REFILL_TIMEOUT = "refill_timeout"
CONF_TELEMETRY_TIMEOUT = "telemetry_timeout"
# Kept as minimum_level internally for backwards compatibility with existing installs.
CONF_MINIMUM_LEVEL = "minimum_level"
CONF_ESTIMATION_RESERVE_LEVEL = "estimation_reserve_level"

DEFAULT_TANK_NAME = "JoJo Water Tank"
DEFAULT_MQTT_TOPIC = "homeassistant/sensor/jojo_tank/state"
DEFAULT_TANK_CAPACITY = 5250.0
DEFAULT_TANK_HEIGHT = 1900.0
DEFAULT_EMPTY_CURRENT = 4.0
DEFAULT_FULL_CURRENT = 11.5
DEFAULT_SENSE_RESISTOR = 120.0
DEFAULT_REFILL_THRESHOLD = 75.0
DEFAULT_REFILL_TIMEOUT = 15.0
DEFAULT_TELEMETRY_TIMEOUT = 15.0
DEFAULT_MINIMUM_LEVEL = 20.0
DEFAULT_ESTIMATION_RESERVE_LEVEL = 10.0

DATA_LATEST = "latest"
DATA_UNSUB = "unsub"
DATA_REFILLING = "refilling"
DATA_LAST_REFILL_AMOUNT = "last_refill_amount"
DATA_LAST_REFILL_TIME = "last_refill_time"
DATA_REFILL_HISTORY = "refill_history"
DATA_REFILL_START_VOLUME = "refill_start_volume"
DATA_REFILL_END_VOLUME = "refill_end_volume"
DATA_PREVIOUS_VOLUME = "previous_volume"
DATA_REFILL_TIMER = "refill_timer"
DATA_ONLINE = "online"
DATA_TELEMETRY_TIMER = "telemetry_timer"
SIGNAL_UPDATE = f"{DOMAIN}_update"

# Optional ambient-weather correction. Defaults are trial settings, not a fitted model.
CONF_TEMPERATURE_COMPENSATION = "temperature_compensation"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_TEMPERATURE_REFERENCE = "temperature_reference"
CONF_TEMPERATURE_COEFFICIENT = "temperature_coefficient"
CONF_TEMPERATURE_CAP = "temperature_cap"
DEFAULT_TEMPERATURE_COMPENSATION = False
DEFAULT_WEATHER_ENTITY = "weather.forecast_home"
DEFAULT_TEMPERATURE_REFERENCE = 20.0
DEFAULT_TEMPERATURE_COEFFICIENT = 5.0
DEFAULT_TEMPERATURE_CAP = 75.0
