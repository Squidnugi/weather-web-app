from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

#the Geocode and Place API from google must be activated for this to work
GOOGLE_API_KEY = 'Google-API-KEY'
OPENWEATHERMAP_API_KEY = 'OPENWEATHERMAP-API-KEY'
WEATHERSTACK_API_KEY = 'WEATHERSTACK-API-KEY'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    input_text = request.args.get('input')
    url = f'https://maps.googleapis.com/maps/api/place/autocomplete/json?input={input_text}&key={GOOGLE_API_KEY}'
    response = requests.get(url)
    return jsonify(response.json())

@app.route('/geocode', methods=['GET'])
def geocode():
    place_id = request.args.get('place_id')
    url = f'https://maps.googleapis.com/maps/api/geocode/json?place_id={place_id}&key={GOOGLE_API_KEY}'
    response = requests.get(url)
    return jsonify(response.json())

@app.route('/weather', methods=['GET'])
def weather():
    place_id = request.args.get('place_id')
    geocode_url = f'https://maps.googleapis.com/maps/api/geocode/json?place_id={place_id}&key={GOOGLE_API_KEY}'
    geocode_response = requests.get(geocode_url).json()
    location = geocode_response['results'][0]['geometry']['location']
    lat, lng = location['lat'], location['lng']

    openweathermap_url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={OPENWEATHERMAP_API_KEY}'
    weatherstack_url = f'http://api.weatherstack.com/current?access_key={WEATHERSTACK_API_KEY}&query={lat},{lng}'

    openweathermap_response = requests.get(openweathermap_url).json()
    weatherstack_response = requests.get(weatherstack_url).json()

    # Extract data from APIs
    weather_data = {
        'openweathermap': {
            'description': openweathermap_response['weather'][0].get('description', 'No description available'),
            'temperature': round(openweathermap_response['main'].get('temp', 0) - 273.15)  # Convert from Kelvin to Celsius
        },
        'weatherstack': {
            'description': weatherstack_response['current'].get('weather_descriptions', ['No description available'])[0],
            'temperature': round(weatherstack_response['current'].get('temperature', 0))  # Already in Celsius
        }
    }

    # Define priorities for weather descriptions
    description_priority = {
        'storm': 3,
        'rain': 2,
        'cloudy': 1,
        'clear': 0
    }

    # Assign weights to each API
    weights = {
        'openweathermap': 0.6,
        'weatherstack': 0.4
    }

    # Rule-based combination logic
    combined_forecast = {'description': {}, 'temperature': {}}

    # Combine data
    for source, data in weather_data.items():
        # Combine descriptions
        description = data['description'].lower()
        if description in combined_forecast['description']:
            combined_forecast['description'][description] += weights[source]
        else:
            combined_forecast['description'][description] = weights[source]

        # Combine temperatures
        temperature = data['temperature']
        if temperature in combined_forecast['temperature']:
            combined_forecast['temperature'][temperature] += weights[source]
        else:
            combined_forecast['temperature'][temperature] = weights[source]

    # Determine the most likely description using rule-based priorities
    most_likely_description = max(
        combined_forecast['description'],
        key=lambda desc: (description_priority.get(desc, -1), combined_forecast['description'][desc])
    )

    # Determine the most likely temperature using weighted average
    most_likely_temperature = sum(
        temp * weight for temp, weight in combined_forecast['temperature'].items()
    ) / sum(combined_forecast['temperature'].values())

    # Format the output
    formatted_forecast = {
        'description': most_likely_description.capitalize(),
        'temperature': round(most_likely_temperature)
    }

    formatted_response = f"Description: {formatted_forecast['description']}, Temperature: {formatted_forecast['temperature']}°C"
    return jsonify({'weather': formatted_response})


if __name__ == '__main__':
    app.run(debug=True)
