# Python Weather CLI Application

## Description

This is a command-line application built with Python that fetches and displays the current weather forecast for a user-provided US ZIP code. It utilizes the `pgeocode` library for converting ZIP codes to geographic coordinates and the official National Weather Service (NWS) API for up-to-date weather data.

This project serves as a portfolio piece to demonstrate skills in Python programming, API integration, and data handling.

## Features

* Prompts the user for a US ZIP code.
* Also allows for a US ZIP code to be passed as a command line argument 
    * This was done to allow for GUI intigration
* Converts the ZIP code to latitude and longitude using `pgeocode`.
* Retrieves weather forecast data from the National Weather Service (NWS) API.
* Displays key weather information such as:
    * Location (Place Name, State)
    * Current/Upcoming period name (e.g., "Tonight", "Thursday")
    * Temperature (in Fahrenheit by default from NWS API)
    * Chance of precipitation
    * Wind speed and direction
    * Short weather forecast description
* Basic error handling for invalid ZIP codes or API issues.

## Technologies Used

* **Language:** Python 3.x
* **Libraries:**
    * `pgeocode`: For offline postal code geocoding.
    * `requests`: For making HTTP requests to the NWS API.
    * `pandas`: (As a dependency of `pgeocode`, used for handling its data output).
* **APIs:**
    * National Weather Service (NWS) API (api.weather.gov)

## Setup

To get this project running locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://www.google.com/search?q=https://github.com/mt-codes-mt/YOUR-REPOSITORY-NAME.git](https://www.google.com/search?q=https://github.com/mt-codes-mt/YOUR-REPOSITORY-NAME.git) 
    # Replace YOUR-REPOSITORY-NAME with the actual name of your GitHub repo
    ```
2.  **Navigate to the project directory:**
    ```bash
    cd YOUR-REPOSITORY-NAME
    ```
3.  **Install dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    # Create a virtual environment (optional but good practice)
    # python -m venv venv
    # source venv/bin/activate  # On Linux/macOS
    # .\venv\Scripts\activate   # On Windows

    # Install required packages
    pip install pgeocode requests pandas
    ```

## Usage

Once the setup is complete, you can run the application from your terminal:

```bash
python WeatherApp.py