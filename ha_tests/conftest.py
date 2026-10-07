"""Use real HA and its MQTT fixtures; no production broker is contacted."""

import pytest
from unittest.mock import Mock


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Allow loading the repository as a custom integration."""


@pytest.fixture(autouse=True)
async def cleanup_entries(hass, mqtt_mock, mqtt_client_mock):
    """Unload our platforms and the fixture's MQTT client before timer checks."""
    # This baseline fixture opens a fake Paho socket on connect. Model its close
    # on disconnect too, so HA's real MQTT misc timer can clean up normally.
    mqtt_client_mock.disconnect.side_effect = lambda: mqtt_client_mock.on_socket_close(
        mqtt_client_mock, None, Mock(fileno=Mock(return_value=-1))
    )
    yield
    for domain in ('jojo_tank', 'mqtt'):
        for entry in hass.config_entries.async_entries(domain):
            await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
