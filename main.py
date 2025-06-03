# main.py

import pandas as pd
import time
import sys
import argparse
from merchant_db import MerchantDB  # Import the MerchantDB class for database operations
from api_manager import LoadSheddingManager  # Import the LoadSheddingManager class to manage API interactions
from logger import log_info, log_error # Import the logger functions to handle logging

# Function to load merchant data from an Excel file
def load_merchants(file_path):
    try:
        # Load the Excel sheet containing merchant data
        data = pd.read_excel(file_path, sheet_name='data')
        # Return relevant columns: latitude, longitude, and merchant UUID
        return data[['latitude', 'longitude', 'merchant_uuid']]
    except FileNotFoundError:
        log_error(f"File not found: {file_path}")
        sys.exit(f"Error: The file {file_path} was not found.")
    except Exception as e:
        log_error(f"Error loading Excel file: {e}")
        sys.exit(f"Error: Failed to load the Excel file due to: {e}")

# Main function that orchestrates the load shedding check loop
def main(file_path, api_token, IsDevelopmentMode):

    db_file = "merchants.db"
    db = MerchantDB(db_file)  # Initialize database connection
    merchants = load_merchants(file_path) # Load merchant data from Excel

    ls_manager = LoadSheddingManager(api_token, IsDevelopmentMode)  # Initialize LoadSheddingManager with the API token

    while True:        
        # Local dictionary to track processed areas to avoid redundant API calls
        processed_areas = {}

        # Loop through each merchant to check their load shedding status
        for index, row in merchants.iterrows():
            lat = row['latitude']
            lon = row['longitude']
            merchant_uuid = row['merchant_uuid']

            try:
                # Obtain area ID based on the merchant's coordinates
                area_info = ls_manager.get_area_id(lat, lon)

                if area_info['area_id'] not in processed_areas:
                    # Fetch load shedding status for this area ID (cached or from API)
                    load_shedding_info = ls_manager.get_area_load_shedding_events(area_info['area_id'])
                    processed_areas[area_info['area_id']] = load_shedding_info
                else:
                    # Use locally cached data if already processed
                    load_shedding_info = processed_areas[area_info['area_id']]

                # Determine if the merchant should be closed due to active load shedding
                if ls_manager.is_load_shedding_active(load_shedding_info):
                    db.add_merchant(merchant_uuid, area_info) # Add merchant to closed list in the database
                    log_info(f"Merchant with UUID {merchant_uuid} is Closed. Area ID: {area_info['area_id']}, Area Name: {area_info['area_name']}")
                else:
                    db.remove_merchant(merchant_uuid, area_info) # Remove merchant from closed list in the database
                    log_info(f"Merchant with UUID {merchant_uuid} is Opened. Area ID: {area_info['area_id']}, Area Name: {area_info['area_name']}")

            except Exception as e:
                log_error(f"Error processing merchant {merchant_uuid}: {e}")

        time.sleep(60) # Wait for 60 seconds before the next iteration

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Monitor load shedding status and manage merchants.')
    parser.add_argument('--excel_file_path', type=str, required=True, help='Path to the Excel file containing merchant data.')
    parser.add_argument('--api_token', type=str, required=True, help='API token for EskomSePush.')
    parser.add_argument('--isDevMode', action='store_true', help='Run in development mode if this flag is set.')

    args = parser.parse_args()

    main(args.excel_file_path, args.api_token, args.isDevMode) # Start the main function
