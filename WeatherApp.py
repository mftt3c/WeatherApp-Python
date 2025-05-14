import pgeocode
import pandas as pd # Import pandas to use pd.isna() for checking NaN
import requests
import json
import sys # Import sys to handle command-line arguments

def zip_code_lookup(zip_code_to_query):

    # Initialize geocoder
    # For the United States, use 'us'.
    # For Great Britain, use 'gb'.
    # For Canada, use 'ca'.
    try:
        nomi = pgeocode.Nominatim('us')
    except Exception as e:
        print(f"Could not initialize geocoder: {e}")
        exit()

    print(f"\nQuerying information for ZIP code: {zip_code_to_query}...")
    location_info = nomi.query_postal_code(zip_code_to_query)

    # --- Check for Valid Location Data ---
    # We consider data valid if key geographical fields like 'latitude' or 'place_name' are NOT NaN.
    # pd.isna() is a reliable way to check for NaN in pandas objects.
    if location_info.empty or pd.isna(location_info.latitude) or pd.isna(location_info.place_name):
        print(f"\nNo valid geographic information found for ZIP code: {zip_code_to_query}")
        print("This might be an invalid ZIP code or not available in the database for the US.")
    else:
        print(f"\nLocation Information Found: \n{location_info.place_name if pd.notna(location_info.place_name) else 'N/A'} {location_info.state_name if pd.notna(location_info.state_name) else 'N/A'}, {location_info.postal_code}")

    # Getting latitude and longitude for your weather lookup (Error handling included)
    if (location_info.empty or pd.isna(location_info.latitude) or pd.isna(location_info.longitude)):
            print("\nCannot proceed to weather lookup due to missing location data.")
            exit()
            return None, None
    else:
        lat = location_info.latitude
        lon = location_info.longitude
        print(f"\nProceeding with Latitude: {lat}, Longitude: {lon} for weather lookup.")
        # Call your get_weather_forecast(lat, lon) function here
        return lat, lon

def get_nws_forecast(latitude, longitude):

    """
    Fetches the weather forecast from the NWS API for given coordinates.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.

    Returns:
        list: A list of forecast periods, or None if an error occurs.
    """

    # --- Construct the User-Agent Header ---
    # Replace with your actual app name and contact email or website
    # This is REQUIRED by the NWS API.
    user_agent = "(WeatherApp/1.0, mt.codes.mt@gmail.com)" 
    headers = {
        'User-Agent': user_agent
    }

 # --- Get the Gridpoint Metadata (to find the forecast URL) ---
    points_url = f"https://api.weather.gov/points/{latitude:.4f},{longitude:.4f}"
    # NWS API typically doesn't want more than 4 decimal places for lat/lon
    try:
        response_points = requests.get(points_url, headers=headers, timeout=10) # 10-second timeout
        response_points.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        points_data = response_points.json()
        
        # Extract the forecast URL from the response
        forecast_url = points_data.get('properties', {}).get('forecast')
        # You could also get 'forecastHourly' if you want an hourly breakdown
        
        if not forecast_url:
            print("Error: Could not find the forecast URL in the NWS points data.")
            print("Raw points data received:")
            print(json.dumps(points_data, indent=2)) # Print raw data for debugging
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while fetching points data: {http_err} - Status: {response_points.status_code}")
        if response_points.content:
            print(f"Error details: {response_points.json()}") # NWS often returns JSON error details
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred while fetching points data: {req_err}")
        return None
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response from points endpoint.")
        return None


    # --- Step 3: Get the Actual Weather Forecast using the extracted URL ---
    try:
        response_forecast = requests.get(forecast_url, headers=headers, timeout=10)
        response_forecast.raise_for_status()
        forecast_data = response_forecast.json()
        
        # The forecast periods are usually in 'properties' -> 'periods'
        return forecast_data.get('properties', {}).get('periods', [])
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while fetching forecast: {http_err} - Status: {response_forecast.status_code}")
        if response_forecast.content:
            try:
                print(f"Error details: {response_forecast.json()}")
            except json.JSONDecodeError:
                print(f"Error details (not JSON): {response_forecast.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred while fetching forecast: {req_err}")
        return None
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response from forecast endpoint.")
        return None

# --- Main Program ---
if __name__ == "__main__":
    # Check if a ZIP code was passed as a command-line argument
    if len(sys.argv) > 1:
        zip_code = sys.argv[1]
        print(f"Using ZIP code: {zip_code}")
    else:
        zip_code = input("Please enter the US ZIP code: ")

    lat, lon = zip_code_lookup(zip_code)
    if lat is None or lon is None:
        print("Could not retrieve latitude and longitude. Exiting.")
        exit()

    get_nws_forecast(lat, lon)  
    
    forecast_periods = get_nws_forecast(lat, lon)
    if forecast_periods:
        print("\n--- Weather Forecast ---")
        # Let's print details for the first few periods
        for period in forecast_periods[:4]: # Display first 3 periods for brevity
            name = period.get('name', 'N/A')
            temp = period.get('temperature', 'N/A')
            temp_unit = period.get('temperatureUnit', '')
            wind_speed = period.get('windSpeed', 'N/A')
            wind_direction = period.get('windDirection', 'N/A')
            short_forecast = period.get('shortForecast', 'N/A')
            chance_of_precip = period.get('probabilityOfPrecipitation', {}).get('value', 'N/A')
            # detailed_forecast = period.get('detailedForecast', 'N/A') # Can be very long
            if chance_of_precip == None:
                chance_of_precip = '0%'
            else:
                chance_of_precip = f"{chance_of_precip}%"

            print(f"\n>> {name}:")
            print(f"   Temperature: {temp}°{temp_unit}")
            print(f"   Chance of Precipitation: {chance_of_precip}.")
            print(f"   Wind: {wind_speed} {wind_direction}")
            print(f"   Forecast: {short_forecast}")
            # print(f"   Details: {detailed_forecast}")
    else:
        print("\nCould not retrieve the weather forecast.")