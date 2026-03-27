"""Motor API integration for Home Assistant.

Exposes a single action: motorapi.lookup_vehicle
which queries the Danish Motor API (v1.motorapi.dk) for vehicle details
by registration number and returns the full data as a service response.
"""
from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_API_KEY,
    API_VEHICLES_URL,
    SERVICE_LOOKUP_VEHICLE,
    ATTR_REGISTRATION_NUMBER,
)

_LOGGER = logging.getLogger(__name__)

def _build_description(data: dict) -> str:
    parts = []
    color = (data.get("color") or "").strip()
    if color and color.lower() != "ukendt":
        parts.append(color.title())
    make = (data.get("make") or "").strip().title().replace("Bmw", "BMW")
    if make:
        parts.append(make)
    model = (data.get("model") or "").strip().title()
    if model:
        parts.append(model)
    return " ".join(parts)


SERVICE_LOOKUP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_REGISTRATION_NUMBER): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Motor API from a config entry."""
    api_key: str = entry.data[CONF_API_KEY]
    session = async_get_clientsession(hass)

    async def handle_lookup_vehicle(call: ServiceCall) -> dict:
        """Handle the lookup_vehicle service call."""
        raw: str = call.data[ATTR_REGISTRATION_NUMBER]
        reg_number = raw.strip().upper()

        if not reg_number:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="empty_registration_number",
            )

        url = f"{API_VEHICLES_URL}/{reg_number}"
        _LOGGER.debug("Fetching vehicle data for %s from %s", reg_number, url)

        try:
            async with session.get(
                url,
                headers={"X-AUTH-TOKEN": api_key},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 404:
                    raise ServiceValidationError(
                        translation_domain=DOMAIN,
                        translation_key="vehicle_not_found",
                        translation_placeholders={"registration_number": reg_number},
                    )
                if resp.status == 401:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="invalid_auth",
                    )
                if resp.status == 429:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="rate_limited",
                    )
                if resp.status != 200:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="api_error",
                        translation_placeholders={"status": str(resp.status)},
                    )

                data: dict = await resp.json()
                data["description"] = _build_description(data)

        except aiohttp.ClientConnectorError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
            ) from err
        except TimeoutError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="timeout",
            ) from err

        _LOGGER.debug("Received vehicle data: %s", data)
        return data

    hass.services.async_register(
        DOMAIN,
        SERVICE_LOOKUP_VEHICLE,
        handle_lookup_vehicle,
        schema=SERVICE_LOOKUP_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    _LOGGER.info("Motor API integration loaded")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, SERVICE_LOOKUP_VEHICLE)
    _LOGGER.info("Motor API integration unloaded")
    return True
