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
2. Add `https://github.com/JBoye/MotorAPI` as category **Integration**
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

### Example: Notify when Frigate recognises a number plate

Triggered by Frigate's `sensor.garage_last_recognized_plate` or `sensor.hoveddor_last_recognized_plate` changing state. The `description` field from the API (e.g. `"Blå Volkswagen Passat"`) is used as the notification message, giving a human-readable summary with no extra templating needed.

```yaml
alias: Nummerplade
description: ""
triggers:
  - trigger: state
    entity_id:
      - sensor.garage_last_recognized_plate
      - sensor.hoveddor_last_recognized_plate
    not_to:
      - unknown
      - unavailable
      - Unknown
      - None
      - ""
conditions: []
actions:
  - action: motorapi.lookup_vehicle
    data:
      registration_number: "{{trigger.to_state.state}}"
    response_variable: vehicle
  - action: notify.mobile_app_jonas_mobil
    data:
      message: >-
        Der er en {{vehicle.description}} i {{ "garagen" if trigger.entity_id ==
        "sensor.garage_last_recognized_plate" else "indkørslen" }}
mode: single
```

### Example: Alert when a non-electric car parks at a charger

Looks up the plate when a charger becomes occupied and notifies if the vehicle is not electric — useful for managing access to EV charging spots.

```yaml
alias: Ikke-elbil ved lader
trigger:
  - platform: state
    entity_id: binary_sensor.charger_occupied
    to: "on"
action:
  - action: motorapi.lookup_vehicle
    data:
      registration_number: "{{ states('sensor.charger_last_plate') }}"
    response_variable: vehicle
  - if:
      - condition: template
        value_template: "{{ vehicle.fuel_type != 'El' }}"
    then:
      - action: notify.mobile_app_my_phone
        data:
          title: "Ikke-elbil ved lader"
          message: >
            {{ vehicle.description }} ({{ vehicle.fuel_type }}) holder ved laderen.
            Nummerplade: {{ vehicle.registration_number }}
```

### Example: Alert when vehicle inspection is due soon

Checks the upcoming inspection date when a plate is scanned and sends a notification if the MOT expires within 30 days — useful for fleet management or keeping track of your own vehicles.

```yaml
alias: Syn snart udløber
trigger:
  - platform: state
    entity_id: sensor.camera_last_recognized_plate
action:
  - action: motorapi.lookup_vehicle
    data:
      registration_number: "{{ trigger.to_state.state }}"
    response_variable: vehicle
  - if:
      - condition: template
        value_template: >
          {{ vehicle.mot_info.next_inspection_date is not none and
             (as_timestamp(vehicle.mot_info.next_inspection_date) - as_timestamp(now())) < 86400 * 30 }}
    then:
      - action: notify.mobile_app_my_phone
        data:
          title: "Syn udløber snart"
          message: >
            {{ vehicle.description }} ({{ vehicle.registration_number }}) skal til syn
            senest {{ vehicle.mot_info.next_inspection_date }}.
            Sidst godkendt: {{ vehicle.mot_info.date }}, km-stand: {{ vehicle.mot_info.mileage }}.
```

### Full response schema

```json
{
  "registration_number": "XX88888",
  "status": "Registreret",
  "status_date": "2020-01-01T00:00:00.000+01:00",
  "type": "Personbil",
  "use": "Privat personkørsel",
  "first_registration": "2018-06-01+02:00",
  "vin": "WAUZZZ000XX000000",
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
  "is_hybrid": true,
  "hybrid_type": "mild",
  "registration_zipcode": "",
  "vehicle_id": 1000000000000001,
  "mot_info": {
    "type": "PeriodiskSyn",
    "date": "2024-06-01",
    "result": "Godkendt",
    "status": "Aktiv",
    "status_date": "2024-06-01",
    "mileage": 80000,
    "next_inspection_date": "2028-01-01"
  },
  "is_leasing": false,
  "leasing_from": null,
  "leasing_to": null,
  "description": "Blå Volkswagen Passat"
}
```

---

## Rate limits

The free Motor API tier has a daily request quota. The integration returns a clear error if the quota is exceeded. You can check your usage at `https://v1.motorapi.dk/usage` (or via the Motor API dashboard).

---

## License

MIT
