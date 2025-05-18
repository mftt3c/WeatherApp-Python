import pgeocode
import pandas as pd
import requests
import json
import sys

def get_location_details(zip_code_to_query, is_gui_call=False):
    """
    Fetches location details (latitude, longitude, place name) for a given ZIP code.

    Args:
        zip_code_to_query (str): The US ZIP code.
        is_gui_call (bool): True if called by GUI, suppresses interactive prints.

    Returns:
        tuple: (latitude, longitude, place_name_formatted, error_message)
               Returns (None, None, None, error_message) if an error occurs.
    """
    latitude, longitude, place_name_formatted, error_message = None, None, None, None
    location_info = None # Initialize to ensure it's always defined

    try:
        nomi = pgeocode.Nominatim('us')
    except Exception as e:
        error_message = f"Could not initialize geocoder: {e}"
        if not is_gui_call:
            print(error_message)
        return latitude, longitude, place_name_formatted, error_message

    if not is_gui_call:
        print(f"\nQuerying information for ZIP code: {zip_code_to_query}...")
    
    try:
        location_info = nomi.query_postal_code(zip_code_to_query)
    except Exception as e: # Catch potential errors during the query itself
        error_message = f"Error querying postal code {zip_code_to_query}: {e}"
        if not is_gui_call:
            print(error_message)
        return latitude, longitude, place_name_formatted, error_message


    if location_info is None or location_info.empty or pd.isna(location_info.latitude) or pd.isna(location_info.longitude):
        error_message = f"No valid geographic information found for ZIP code: {zip_code_to_query}"
        if not is_gui_call:
            print(f"\n{error_message}")
            print("This might be an invalid ZIP code or not available in the database for the US.")
    else:
        latitude = str(location_info.latitude) # Ensure string for JSON
        longitude = str(location_info.longitude) # Ensure string for JSON
        
        place_name_str = location_info.place_name if pd.notna(location_info.place_name) else "N/A"
        state_code_str = location_info.state_code if pd.notna(location_info.state_code) else "" # Use state_code for abbreviation
        place_name_formatted = f"{place_name_str}, {state_code_str}".strip(", ") # Avoid trailing comma if state_code is empty

        if not is_gui_call:
            print(f"\nLocation Information Found: {place_name_formatted}")
            print(f"Proceeding with Latitude: {latitude}, Longitude: {longitude} for weather lookup.")
            
    return latitude, longitude, place_name_formatted, error_message


def get_nws_forecast_data(latitude, longitude, is_gui_call=False):
    """
    Fetches the weather forecast from the NWS API for given coordinates.

    Args:
        latitude (str): Latitude of the location.
        longitude (str): Longitude of the location.
        is_gui_call (bool): True if called by GUI, suppresses interactive prints.

    Returns:
        tuple: (list_of_forecast_period_dicts, error_message)
               Returns (None, error_message) if an error occurs.
    """
    forecast_periods_data = None
    error_message = None

    user_agent = "(WeatherAppPy/1.1, mt-codes-mt@gmail.com)" # Updated version/email
    headers = {'User-Agent': user_agent}

    points_url = f"https://api.weather.gov/points/{float(latitude):.4f},{float(longitude):.4f}"
    
    if not is_gui_call:
        print(f"Fetching gridpoint data from: {points_url}")

    try:
        response_points = requests.get(points_url, headers=headers, timeout=15)
        response_points.raise_for_status()
        points_data = response_points.json()
        forecast_url = points_data.get('properties', {}).get('forecast')

        if not forecast_url:
            error_message = "Error: Could not find the forecast URL in the NWS points data."
            if not is_gui_call:
                print(error_message)
                print("Raw points data received:")
                print(json.dumps(points_data, indent=2))
            return None, error_message

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error fetching points: {http_err} (Status: {response_points.status_code if 'response_points' in locals() else 'Unknown'})"
        if not is_gui_call: print(error_message)
        return None, error_message
    except requests.exceptions.RequestException as req_err:
        error_message = f"Request error fetching points: {req_err}"
        if not is_gui_call: print(error_message)
        return None, error_message
    except json.JSONDecodeError:
        error_message = "Error: Could not decode JSON from points endpoint."
        if not is_gui_call: print(error_message)
        return None, error_message
    except Exception as e:
        error_message = f"Unexpected error fetching points: {e}"
        if not is_gui_call: print(error_message)
        return None, error_message


    if not is_gui_call:
        print(f"Fetching actual forecast from: {forecast_url}")
    try:
        response_forecast = requests.get(forecast_url, headers=headers, timeout=15)
        response_forecast.raise_for_status()
        forecast_data = response_forecast.json()
        
        raw_periods = forecast_data.get('properties', {}).get('periods', [])
        forecast_periods_data = []
        for period in raw_periods:
            # Prepare data to match VB.NET PythonForecastPeriod class
            chance_val = period.get('probabilityOfPrecipitation', {}).get('value')
            if chance_val is None: # NWS API returns null if no PoP
                chance_of_precip_str = "0%"
            else:
                chance_of_precip_str = f"{chance_val}%"

            forecast_periods_data.append({
                "Name": period.get('name', 'N/A'),
                "Temperature": period.get('temperature', 0), # Default to 0 if missing
                "TemperatureUnit": period.get('temperatureUnit', 'F'),
                "WindSpeed": period.get('windSpeed', 'N/A'),
                "WindDirection": period.get('windDirection', 'N/A'),
                "ShortForecast": period.get('shortForecast', 'N/A'),
                "ChanceOfPrecipitation": chance_of_precip_str
            })
        
    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error fetching forecast: {http_err} (Status: {response_forecast.status_code if 'response_forecast' in locals() else 'Unknown'})"
        if not is_gui_call: print(error_message)
        return None, error_message
    except requests.exceptions.RequestException as req_err:
        error_message = f"Request error fetching forecast: {req_err}"
        if not is_gui_call: print(error_message)
        return None, error_message
    except json.JSONDecodeError:
        error_message = "Error: Could not decode JSON from forecast endpoint."
        if not is_gui_call: print(error_message)
        return None, error_message
    except Exception as e:
        error_message = f"Unexpected error fetching forecast details: {e}"
        if not is_gui_call: print(error_message)
        return None, error_message
        
    return forecast_periods_data, error_message


# --- Main Program ---
if __name__ == "__main__":
    # Determine if called by GUI (if a ZIP code argument is provided)
    # sys.argv[0] is the script name, sys.argv[1] would be the first argument
    is_gui_call = len(sys.argv) > 1 
    zip_code_arg = None

    output_data_for_gui = {
        "LocationName": None,
        "Latitude": None,
        "Longitude": None,
        "ErrorMessage": None,
        "ForecastPeriods": [] # Ensure it's an empty list, not null
    }

    if is_gui_call:
        zip_code_arg = sys.argv[1]
    else:
        zip_code_arg = input("Please enter the US ZIP code: ")

    # --- Step 1: Get Location Details ---
    lat, lon, location_name, loc_error = get_location_details(zip_code_arg, is_gui_call)

    if loc_error:
        output_data_for_gui["ErrorMessage"] = loc_error
        if is_gui_call:
            print(json.dumps(output_data_for_gui))
        else:
            # Interactive mode already printed the error in get_location_details
            pass # Or print a summary error
        sys.exit(1) # Exit with an error code if location fails

    output_data_for_gui["LocationName"] = location_name
    output_data_for_gui["Latitude"] = lat
    output_data_for_gui["Longitude"] = lon
    
    # --- Step 2: Get Weather Forecast ---
    forecast_periods, weather_error = get_nws_forecast_data(lat, lon, is_gui_call)

    if weather_error:
        # Combine with location error if it exists, or set it
        combined_error = output_data_for_gui["ErrorMessage"] + f"; {weather_error}" if output_data_for_gui["ErrorMessage"] else weather_error
        output_data_for_gui["ErrorMessage"] = combined_error
        if is_gui_call:
            print(json.dumps(output_data_for_gui))
        else:
             # Interactive mode already printed the error in get_nws_forecast_data
            pass
        sys.exit(1) # Exit with an error code if weather fails

    if forecast_periods:
        output_data_for_gui["ForecastPeriods"] = forecast_periods
    
    # --- Step 3: Output ---
    if is_gui_call:
        # Print the entire collected data as a single JSON string for VB.NET
        print(json.dumps(output_data_for_gui))
    else:
        # Interactive mode: Print formatted output to console
        if output_data_for_gui["ErrorMessage"]:
            print(f"\nError: {output_data_for_gui['ErrorMessage']}")
        
        if output_data_for_gui["ForecastPeriods"]:
            print("\n--- Weather Forecast ---")
            for period in output_data_for_gui["ForecastPeriods"][:4]: # Display first 4 periods
                print(f"\n>> {period.get('Name', 'N/A')}:")
                print(f"   Temperature: {period.get('Temperature', 'N/A')}°{period.get('TemperatureUnit', 'F')}")
                print(f"   Chance of Precipitation: {period.get('ChanceOfPrecipitation', 'N/A')}")
                print(f"   Wind: {period.get('WindSpeed', 'N/A')} {period.get('WindDirection', 'N/A')}")
                print(f"   Forecast: {period.get('ShortForecast', 'N/A')}")
        elif not output_data_for_gui["ErrorMessage"]: # Only print this if no other error was more specific
            print("\nCould not retrieve the weather forecast details.")

