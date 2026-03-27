"""Config flow for the Motor API integration."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_API_KEY, API_USAGE_URL


async def _validate_api_key(hass: HomeAssistant, api_key: str) -> str | None:
    """
    Validate the API key by hitting the free /usage endpoint.
    Returns an error key string on failure, or None on success.
    """
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            API_USAGE_URL,
            headers={"X-AUTH-TOKEN": api_key},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 401:
                return "invalid_auth"
            if resp.status != 200:
                return "cannot_connect"
    except aiohttp.ClientConnectorError:
        return "cannot_connect"
    except aiohttp.ClientError:
        return "cannot_connect"
    except TimeoutError:
        return "timeout"

    return None


class MotorApiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Motor API."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            error = await _validate_api_key(self.hass, api_key)

            if error is None:
                # Prevent duplicate entries
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Motor API",
                    data={CONF_API_KEY: api_key},
                )

            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "api_url": "https://v1.motorapi.dk/doc/",
            },
        )
