from fastapi import FastAPI,HTTPException, Query
import requests
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import joblib
import numpy as np
from typing import List

app = FastAPI()

model = joblib.load('./ml_model/without_pcm.pkl')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# API Keys (Replace with your actual OpenWeatherMap API key)
OPENWEATHERMAP_API_KEY = "b7bf0702e15026adf3b50f268a82d31d"

# Function to get weather data from OpenWeatherMap
def get_weather_data(lat: float, lon: float):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "location": data.get("name", "Unknown"),
            #"temperature": data["main"]["temp"],
            #"humidity": data["main"]["humidity"],
            #"wind_speed": data["wind"]["speed"],
        }
    else:
        return {"error": "Failed to fetch weather data"}

# Function to get solar radiation from NASA POWER API
def get_solar_radiation(lat: float, lon: float, date: str):
    url = f"https://power.larc.nasa.gov/api/temporal/hourly/point?latitude={lat}&longitude={lon}&start={date}&end={date}&parameters=ALLSKY_SFC_SW_DWN&community=re&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        radiation_data = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]

        if not radiation_data:
            return {"error": "No solar radiation data available"}

        radiation_30min_intervals = {}

        for hour in range(9, 20):  # Loop from 9:00 AM (09) to 8:00 PM (20)
            hour_key = f"{date}{hour:02d}"
            next_hour_key = f"{date}{hour+1:02d}"

            # Get radiation values at full hour
            R1 = radiation_data.get(hour_key)
            R2 = radiation_data.get(next_hour_key)

            if R1 is None or R2 is None:
                continue  # Skip if data is missing

            # Store full-hour radiation
            radiation_30min_intervals[f"{hour}:00"] = R1

            # Interpolate for 30-minute interval
            R_half = R1 + (R2 - R1) / 2  # Linear interpolation
            radiation_30min_intervals[f"{hour}:30"] = R_half

        # Add the last value (8:30 PM)
        last_key = f"{date}20"
        if last_key in radiation_data:
            radiation_30min_intervals["20:30"] = radiation_data[last_key]

        return radiation_30min_intervals
    else:
        return {"error": "Failed to fetch solar radiation data"}



# API Endpoint
@app.get("/api/weather")
def get_weather(lat: float, lon: float, date: str):
    weather_data = get_weather_data(lat, lon)
    radiation_data = get_solar_radiation(lat, lon, date)

    if "error" in weather_data:
        return {"error": weather_data["error"]}
    if "error" in radiation_data:
        return {"error": radiation_data["error"]}

    return {
        "location": weather_data["location"], 
        "solar_radiation": radiation_data  
    }



@app.get("/api/without_pcm")
def predict(total_minutes: List[int]=Query(...), solar_radiation: List[float]=Query(...)):
    # Validate input lengths
    if len(total_minutes) != len(solar_radiation):
        raise HTTPException(status_code=400, detail="Input lists must have the same length.")
        
    # Prepare the input data for prediction as a 2D NumPy array
    # Each row corresponds to [total_minutes, solar_radiation]
    X = np.array(list(zip(total_minutes, solar_radiation)))
    
    # Make predictions using the loaded model
    y_pred = model.predict(X)
    
    # Create a list of prediction dictionaries for each input row
    predictions = [
        {"water_temp": float(pred[0]), "box_temp": float(pred[1])} 
        for pred in y_pred
    ]
    
    # Return the predictions as JSON response
    return {"predictions": predictions}