from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta
import geocoder
import math
import os
from dotenv import load_dotenv
from timezonefinder import TimezoneFinder
import pytz

# Load .env file
load_dotenv()

app = Flask(__name__)


class WeatherPlanner:
    def __init__(self):
        # Get API keys from .env file
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.opencage_api_key = os.getenv('OPENCAGE_API_KEY')
        self.tf = TimezoneFinder()

        # Weather scoring rules
        self.excellent_conditions = {'clear', 'sunny'}
        self.good_conditions = {'few clouds', 'scattered clouds', 'broken clouds', 'overcast clouds'}
        self.bad_conditions = {'rain', 'drizzle', 'snow', 'thunderstorm', 'heavy rain'}

        self.ideal_temp_range = (18, 28)  # °C
        self.max_wind_speed = 15  # m/s
        self.max_precipitation_prob = 30  # %

    def get_coordinates(self, country, city, place):
        try:
            query = f"{place}, {city}, {country}" if place else f"{city}, {country}"
            g = geocoder.opencage(query, key=self.opencage_api_key)
            return g.latlng if g.ok else None
        except:
            return None

    def get_weather_forecast(self, lat, lon, date):
        try:
            timezone_str = self.tf.timezone_at(lat=lat, lng=lon) or 'UTC'
            tz = pytz.timezone(timezone_str)
            local_date = tz.localize(date)

            url = "https://api.openweathermap.org/data/3.0/onecall"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key,
                'units': 'metric',
                'exclude': 'minutely,hourly,alerts'
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            target_date = local_date.date()
            for daily_data in data.get('daily', []):
                forecast_date = datetime.fromtimestamp(daily_data['dt'], tz=tz).date()
                if forecast_date == target_date:
                    return {
                        'temperature': daily_data['temp']['day'],
                        'description': daily_data['weather'][0]['description'],
                        'humidity': daily_data['humidity'],
                        'wind_speed': daily_data.get('wind_speed', 0),
                        'precipitation_prob': daily_data.get('pop', 0) * 100,
                        'icon': daily_data['weather'][0]['icon']
                    }
            return None
        except:
            return None

    def calculate_weather_score(self, weather_data):
        if not weather_data:
            return 0

        temp = weather_data['temperature']
        if self.ideal_temp_range[0] <= temp <= self.ideal_temp_range[1]:
            temp_score = 100
        else:
            temp_score = max(0, 100 - abs(temp - 24) * 5)

        description = weather_data['description'].lower()
        if any(excellent in description for excellent in self.excellent_conditions):
            condition_score = 100
        elif any(good in description for good in self.good_conditions):
            condition_score = 80
        elif any(bad in description for bad in self.bad_conditions):
            condition_score = 30
        else:
            condition_score = 60

        wind_speed = weather_data['wind_speed']
        wind_score = max(0, 100 - (wind_speed / self.max_wind_speed) * 50)

        precip_prob = weather_data['precipitation_prob']
        precip_score = max(0, 100 - (precip_prob / 100) * 50)

        final_score = (temp_score * 0.4 + condition_score * 0.3 + wind_score * 0.15 + precip_score * 0.15)
        return round(final_score, 1)

    def get_weekly_forecast(self, lat, lon, start_date):
        weekly_forecast = []
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            weather = self.get_weather_forecast(lat, lon, current_date)
            if weather:
                weekly_forecast.append({
                    'date': current_date,
                    'weather': weather,
                    'score': self.calculate_weather_score(weather)
                })
        return weekly_forecast

    def find_nearby_locations(self, city, country):
        try:
            base_coords = self.get_coordinates(country, city, city)
            if not base_coords:
                return []

            city_mappings = {
                'london': ['Cambridge', 'Oxford', 'Brighton', 'Reading'],
                'new york': ['Newark', 'Jersey City', 'Yonkers', 'Stamford'],
                'paris': ['Versailles', 'Orly', 'Saint-Denis', 'Boulogne-Billancourt'],
                'tokyo': ['Yokohama', 'Kawasaki', 'Saitama', 'Chiba'],
                'sydney': ['Parramatta', 'Newcastle', 'Wollongong', 'Penrith']
            }

            city_lower = city.lower()
            fallback_cities = city_mappings.get(city_lower, [city])

            nearby_locations = []
            for nearby_city in fallback_cities[:4]:
                coords = self.get_coordinates(country, nearby_city, nearby_city)
                if coords:
                    distance = self.calculate_distance(base_coords, coords)
                    if distance <= 100:
                        nearby_locations.append({
                            'name': nearby_city,
                            'coords': coords,
                            'distance': round(distance, 1)
                        })
            return nearby_locations
        except:
            return []

    def calculate_distance(self, coord1, coord2):
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return round(6371 * 2 * math.asin(math.sqrt(a)), 1)


weather_planner = WeatherPlanner()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/check-weather', methods=['POST'])
def check_weather():
    try:
        country = request.form['country']
        city = request.form['city']
        place = request.form.get('place', city)
        event_date_str = request.form['event_date']

        event_date = datetime.strptime(event_date_str, '%Y-%m-%d')

        coordinates = weather_planner.get_coordinates(country, city, place)
        if not coordinates:
            return render_template('results.html', error="Location not found")

        weather_data = weather_planner.get_weather_forecast(coordinates[0], coordinates[1], event_date)
        if not weather_data:
            return render_template('results.html', error="Weather data not available")

        score = weather_planner.calculate_weather_score(weather_data)

        weekly_forecast = weather_planner.get_weekly_forecast(coordinates[0], coordinates[1], event_date)
        nearby_locations = weather_planner.find_nearby_locations(city, country)

        better_days = [day for day in weekly_forecast if day['score'] > score + 10]
        better_days.sort(key=lambda x: x['score'], reverse=True)

        better_locations = []
        for location in nearby_locations:
            loc_weather = weather_planner.get_weather_forecast(
                location['coords'][0], location['coords'][1], event_date
            )
            if loc_weather:
                loc_score = weather_planner.calculate_weather_score(loc_weather)
                if loc_score > score + 5:
                    better_locations.append({
                        'name': location['name'],
                        'weather': loc_weather,
                        'score': loc_score,
                        'distance': location['distance']
                    })

        better_locations.sort(key=lambda x: x['score'], reverse=True)

        return render_template('results.html',
                               country=country,
                               city=city,
                               place=place,
                               event_date=event_date_str,
                               weather_data=weather_data,
                               score=score,
                               better_days=better_days[:3],
                               better_locations=better_locations[:3]
                               )

    except Exception as e:
        return render_template('results.html', error=str(e))


if __name__ == '__main__':
    # Debug: show if keys are loaded
    print("OpenWeather Key:", os.getenv("OPENWEATHER_API_KEY"))
    print("OpenCage Key:", os.getenv("OPENCAGE_API_KEY"))

    app.run(debug=True)
