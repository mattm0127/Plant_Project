import requests
import json
from pathlib import Path
from decouple import config

def generate_weather():
        """Generate the weather database from weather.visualcrossing.com."""
        api_key = config("API_KEY")
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest"
        url += f"/services/timeline/Haverstraw%2C%20New%20York?unitGroup=us&"
        url += f"key={api_key}&include=fcst%2Chours%2Calerts%2Ccurrent"
        response = requests.get(url)
        weather = response.json()
        path = Path('weather.json')
        data = json.dumps(weather)
        path.write_text(data)
        print('done')
