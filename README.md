# Budapest GO (BKK) for Home Assistant

Modern Home Assistant custom integration for Budapest public transport (BKK).

## Features
- **UI-based configuration:** Add stops via Settings -> Integrations.
- **One API Key, Many Stops:** Manage all your favorite stops in one place.
- **Built-in Lovelace Card:** Includes a custom card that replicates the BP GO app look.

## Installation
1. Add this repository to HACS as a Custom Repository.
2. Install "Budapest GO (BKK)".
3. Restart Home Assistant.

## Configuration
1. Go to **Settings -> Integrations**.
2. Click **Add Integration** and search for **Budapest GO**.
3. Enter your BKK API Key.
4. Use the **Configure** button on the integration to add individual stops by their Stop ID.

## Lovelace Card
Add the following as a Resource in Home Assistant:
- **URL:** `/bkk_ha/bkk-stop-card.js`
- **Type:** `JavaScript Module`
