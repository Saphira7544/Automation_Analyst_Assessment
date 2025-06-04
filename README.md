
# Automation Analyst Assessment - Load Shedding Management System 
### By: Isabel Castelo
For: Uber / Uber Eats - EMEA

### Overview
 This project was developed as part of a recruitment test for the Automation Analyst position at Uber Eats - EMEA. The goal is to automate the process of managing Uber Eats merchants based on load shedding status in South Africa. 
 The solution leverages the EskomSePush API to monitor load shedding events in specific areas and temporarily closes merchants in affected zones.

### Key Features:

**Real-time Load Shedding Monitoring:** Fetches and processes load shedding status using GPS coordinates for each merchant.
**Merchant Management:** Automatically closes or reopens merchants based on the current load shedding schedule.
**Error Handling & Logging:** Robust error handling and logging mechanisms to ensure reliability and traceability.
**Caching:** Implements caching mechanisms to reduce API calls and improve efficiency while maintaining data freshness.
		
### Requirements
To run this script, you'll need the following Python libraries:

  - pandas
  - requests
  - cachetools
  - sqlite3 (standard library)
  - logging (standard library)
  - argparse (standard library)
  - re (standard library)
	
You can install the non-standard libraries using pip:

```
pip install pandas requests cachetools
```

### Project Structure
- **main.py:** The entry point of the application. Handles loading merchant data, iterating over merchants, and calling necessary functions to check load shedding status and update merchant status.
- **merchant_db.py:** Contains the MerchantDB class, which manages the SQLite database. This includes adding and removing merchants and logging operations.
- **api_manager.py:** Contains the LoadSheddingManager class, which interacts with the EskomSePush API to retrieve area IDs and load shedding events. It also manages the caching of API responses.
- **logger.py:** Contains utility functions for logging information and errors. Logs are written to merchant_operations.log.
  
### Usage  

To run the script, use the command line with the following arguments:  
```
python main.py --excel_file_path 'path/to/your/excel/file.xlsx' --api_token 'your_api_token_here' [--isDevMode]  
```

**Arguments**  
- ***--excel_file_path:*** Required. The path to the Excel file containing merchant data. The file should have a sheet named data with columns latitude, longitude, and merchant_uuid.  
- ***--api_token:*** Required. Your API token for accessing the EskomSePush API.  
- ***--isDevMode:*** Optional. If this flag is included, the script runs in development mode, which may include test data or simulate future events. If omitted, the script runs in production mode.  

**Example:**  
```
  python main.py --excel_file_path 'data/merchants.xlsx' --api_token '6AF094ED-D8C941C4-A432D3C8-1F7A6FAE' --isDevMode
```

### Error Handling and Logging

Operations and errors are logged to merchant_operations.log with timestamps. This log file will contain information about:  
		
  - When merchants are closed or opened.  
  - The area ID and name for each operation.  
  - If the Excel file is not found or cannot be loaded, the script will log an error and exit.  
  - Errors during API calls or database operations are logged for review.	  	
  - Any errors encountered during execution.  
		
### Development and Testing   

The script is designed to be robust and efficient, handling intermittent connectivity and minimizing API calls through caching. Development mode can be toggled using the --isDevMode flag to test different scenarios.  
	
### Future Enhancements:  
- **Scalability:** Although the solution is designed to be efficient, further optimizations may be required as the project scales to handle more merchants across different cities.  
- **API Call Optimization:**  
	- Additional strategies, such as grouping merchants close to each other and assuming they're from the same area before making API calls, could further reduce the number of API requests.  
	- Verify the number of available calls left to the API, and after a certain threshold increases the time the information is cached to save on the number of API requests.  
	- Implementing a robust solution that does more frequently API calls to areas with active load shedding, and less frequent API calls to areas without currently active load shedding  
- **Detailed Reporting:** Enhancements to the logging system to include more granular details about each merchant's status and load shedding history.  
  
