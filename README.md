# Motor API — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A [Home Assistant](https://www.home-assistant.io/) custom integration that exposes the [Danish Motor API](https://v1.motorapi.dk/doc/) as a single **action** (service), allowing you to look up vehicle details by registration number from scripts and automations.

---

## Features

- **One action**: `motorapi.lookup_vehicle` — takes a registration number, returns full vehicle data as a response variable.
- Config-flow setup: just enter your API key, no YAML required.
- Proper error handling: 404 (plate not found), 401 (bad key), 429 (quota exceeded), network errors.

---

## Installation via HACS

1. Open **HACS** → **Integrations** → ⋮ menu → **Custom repositories**
2. Add `https://github.com/JBoye/ha-motorapi` as category **Integration**
3. Search for **Motor API** and install
4. Restart Home Assistant

### Manual installation

Copy the `custom_components/motorapi/` folder into your HA config's `custom_components/` directory and restart.

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Motor API**
3. Enter your API key from [motorapi.dk](https://v1.motorapi.dk/doc/)

---

## Usage

### Action: `motorapi.lookup_vehicle`

| Field | Type | Required | Description |
|---|---|---|---|
| `registration_number` | `string` | ✅ | Danish number plate, e.g. `AB12345` |

The action **returns a response** with the full vehicle data object. Use `response_variable` in scripts/automations to capture it.

### Example: Script with response variable

```yaml
sequence:
  - action: motorapi.lookup_vehicle
    data:
      registration_number: "AB12345"
    response_variable: vehicle

  - if:
      - condition: template
        value_template: "{{ vehicle.fuel_type == 'El' }}"
    then:
      - action: notify.mobile_app_my_phone
        data:
          message: "{{ vehicle.make }} {{ vehicle.model }} er elektrisk 🔋"
    else:
      - action: notify.mobile_app_my_phone
        data:
          message: >
            {{ vehicle.make }} {{ vehicle.model }} ({{ vehicle.fuel_type }}).
            Næste syn: {{ vehicle.mot_info.next_inspection_date }}
```

### Example: Automation trigger with response

```yaml
alias: Tjek køretøj ved ankomst
trigger:
  - platform: state
    entity_id: input_text.gæstens_nummerplade
    to: ~
action:
  - action: motorapi.lookup_vehicle
    data:
      registration_number: "{{ trigger.to_state.state }}"
    response_variable: vehicle
  - action: notify.persistent_notification
    data:
      title: "Køretøjsoplysninger"
      message: >
        {{ vehicle.make }} {{ vehicle.model }} {{ vehicle.variant }}
        Farve: {{ vehicle.color }}
        Brændstof: {{ vehicle.fuel_type }}
        Syn: {{ vehicle.mot_info.result }} — næste: {{ vehicle.mot_info.next_inspection_date }}
```

### Full response schema

```json
{
  "registration_number": "DD97767",
  "status": "Registreret",
  "status_date": "2021-10-20T09:56:17.000+02:00",
  "type": "Personbil",
  "use": "Privat personkørsel",
  "first_registration": "2016-04-12+02:00",
  "vin": "WVWZZZ3CZGE193129",
  "own_weight": null,
  "cerb_weight": 1876,
  "total_weight": 2250,
  "axels": 2,
  "pulling_axels": 1,
  "seats": 5,
  "coupling": true,
  "trailer_maxweight_nobrakes": 750,
  "trailer_maxweight_withbrakes": 1900,
  "doors": 4,
  "make": "VOLKSWAGEN",
  "model": "PASSAT",
  "variant": "1,4 gte hybrid",
  "model_type": "3c",
  "model_year": 0,
  "color": null,
  "chassis_type": "Stationcar",
  "engine_cylinders": 4,
  "engine_volume": 1395,
  "engine_power": 115,
  "fuel_type": "Benzin",
  "is_hybrid": false,
  "hybrid_type": "mild",
  "registration_zipcode": "",
  "vehicle_id": 9000000004225773,
  "mot_info": {
    "type": "PeriodiskSyn",
    "date": "2025-10-06",
    "result": "Godkendt",
    "status": "Aktiv",
    "status_date": "2025-10-06",
    "mileage": 165000,
    "next_inspection_date": "2027-10-06"
  },
  "is_leasing": false,
  "leasing_from": null,
  "leasing_to": null
}
```

---

## Rate limits

The free Motor API tier has a daily request quota. The integration returns a clear error if the quota is exceeded. You can check your usage at `https://v1.motorapi.dk/usage` (or via the Motor API dashboard).

---

## License

MIT
