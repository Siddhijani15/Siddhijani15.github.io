# Weatherly

A clean, modern, and minimalist weather web application built with
HTML, CSS, and JavaScript. It retrieves live weather data from the
OpenWeatherMap API based on a user-provided city, country, and API key.

## Features

- Enter a city and country to look up current weather.
- Provide your own OpenWeatherMap API key through the interface
  (no hard-coded keys).
- Displays:
  - Location name
  - Current temperature (converted from Kelvin to Celsius)
  - Current weather condition
  - Additional details: feels like, humidity, wind speed, and pressure
- Useful error messages for:
  - Missing fields
  - Location not found (404)
  - Invalid API key (401)
  - General request failures
- Fully responsive, minimalist design with a gradient background.

## Project Structure

```
Weatherly/
├── index.html    # Main page structure
├── styles.css    # Styling and responsive layout
├── script.js     # Form handling and API integration
└── README.md     # This file
```

## How to Run

This is a static web application — no build step or server is required.

### Option 1: Open in a browser
1. Open the `index.html` file directly in your browser
   (double-click the file, or drag it into a browser window).

### Option 2: Serve with a local server (recommended)
Some browsers restrict `fetch` when loading files via `file://`.
If you see CORS or network errors, run a simple local server:

**Using Python 3:**
```bash
python3 -m http.server 8000
```
Then visit `http://localhost:8000` in your browser.

**Using Node.js (if installed):**
```bash
npx serve .
```

## Getting an OpenWeatherMap API Key

1. Go to [https://openweathermap.org/api](https://openweathermap.org/api)
   and sign up for a free account.
2. After signing up, you will receive an API key (you may need to
   activate it via email).
3. Copy the key and paste it into the "OpenWeatherMap API Key" field
   in the application.

## How to Use

1. Enter a city name (e.g., `London`).
2. Enter a country code or name (e.g., `GB`).
3. Paste your OpenWeatherMap API key.
4. Click **Get Weather** to see the current conditions.

## Dependencies

- OpenWeatherMap API (requires a free API key)
- No external JavaScript libraries or build tools required.

## License

This project is for educational purposes.