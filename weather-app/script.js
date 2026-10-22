/* Weatherly - JavaScript */
const form = document.getElementById('weather-form');
const messageEl = document.getElementById('message');
const weatherResult = document.getElementById('weather-result');

const WEATHER_API_BASE = 'https://api.openweathermap.org/data/2.5/weather';

// OpenWeatherMap icon mapping
const ICON_BASE = 'https://openweathermap.org/img/wn';

function getIconUrl(iconCode) {
  return `${ICON_BASE}/${iconCode}@2x.png`;
}

function kelvinToCelsius(kelvin) {
  return Math.round(kelvin - 273.15);
}

function showMessage(text, type = 'error') {
  messageEl.textContent = text;
  messageEl.className = `message show ${type}`;
}

function clearMessage() {
  messageEl.textContent = '';
  messageEl.className = 'message';
}

function hideWeather() {
  weatherResult.classList.add('hidden');
}

function showWeather(data) {
  const locationName = `${data.name}, ${data.sys.country}`;
  const tempC = kelvinToCelsius(data.main.temp);
  const feelsLikeC = kelvinToCelsius(data.main.feels_like);
  const condition = data.weather[0].description;
  const iconCode = data.weather[0].icon;

  document.getElementById('location-name').textContent = locationName;
  document.getElementById('temperature').textContent = tempC;
  document.getElementById('feels-like').textContent = `${feelsLikeC}°C`;
  document.getElementById('humidity').textContent = `${data.main.humidity}%`;
  document.getElementById('wind-speed').textContent = `${data.wind.speed} m/s`;
  document.getElementById('pressure').textContent = `${data.main.pressure} hPa`;
  document.getElementById('condition-text').textContent = condition;
  document.getElementById('weather-icon').src = getIconUrl(iconCode);
  document.getElementById('weather-icon').alt = condition;

  weatherResult.classList.remove('hidden');
}

async function fetchWeather(city, country, apiKey) {
  const url = `${WEATHER_API_BASE}?q=${encodeURIComponent(city)},${encodeURIComponent(country)}&appid=${encodeURIComponent(apiKey)}`;

  const response = await fetch(url);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Location not found. Please check the city and country.');
    }
    if (response.status === 401) {
      throw new Error('Invalid API key. Please check your OpenWeatherMap API key.');
    }
    throw new Error('Unable to retrieve weather data. Please try again later.');
  }

  return response.json();
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const city = document.getElementById('city').value.trim();
  const country = document.getElementById('country').value.trim();
  const apiKey = document.getElementById('api-key').value.trim();

  if (!city || !country || !apiKey) {
    showMessage('Please fill in all fields.', 'error');
    return;
  }

  // Disable button and show loading state
  const submitBtn = form.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Loading...';
  clearMessage();
  hideWeather();

  try {
    const data = await fetchWeather(city, country, apiKey);
    showWeather(data);
    showMessage('Weather updated successfully.', 'success');
    // Clear success message after a few seconds
    setTimeout(clearMessage, 4000);
  } catch (err) {
    showMessage(err.message, 'error');
    hideWeather();
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Get Weather';
  }
});