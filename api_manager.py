# api_manager.py

import requests
import re
from cachetools import TTLCache
from datetime import datetime, timezone
from logger import log_error # Import the logger functions

class LoadSheddingManager:
    def __init__(self, api_token, IsDevelopmentMode):
        # In order to reduce API calls while still promoting data freshness and integrity the following approach was taken
        #
        #   - Area IDs based on the GPS coordinates provided are important and necessary information, however it doesn't change frequently
        #           => Area IDs will be cached for 24h, meaning that we will only have to fetch it once per day
        #
        #   - Load shedding status per area ID is also an important and necessary information, however it may change rather frequently
        #           => Load shedding events per area ID is stored for 30 minutes

        self.api_token = api_token
        self.area_info_cache = TTLCache(maxsize=1000, ttl=86400)  # Cache area IDs for 24 hours
        self.events_cache = TTLCache(maxsize=1000, ttl=1800)  # Cache load shedding events for 30 minutes

        self.load_shedding_info = {}  # Dictionary to hold load shedding info

        # Class variable to define if the API is called in development or test mode
        self.IsDevelopmentMode = IsDevelopmentMode

    def get_area_id(self, lat, lon):
        """
        Function to get area id based on GPS coordinates either from API or from cache.
        The result is cached for 24 hours to reduce API calls.
        """
        if (lat, lon) in self.area_info_cache:
            return self.area_info_cache[(lat, lon)]
            
        # API call to fetch area ID
        apiURL = f'https://developer.sepush.co.za/business/2.0/areas_nearby?lat={lat}&lon={lon}'

        try:
            response = requests.get(apiURL, headers={'Token': self.api_token})
            response.raise_for_status()  # Check for HTTP errors
            
            area_id = response.json()['areas'][0]['id']  
            area_name = response.json()['areas'][0]['name']
            area_info = {
                'area_id': area_id,
                'area_name': area_name
            }
            self.area_info_cache[(lat, lon)] = area_info
            return area_info

        except requests.exceptions.HTTPError as err:
            exception = f'HTTP error occurred while fetching area ID: {err}'
            log_error(exception)  # Log HTTP errors
            raise ValueError(exception)
        except Exception as e:
            exception = f'An error occurred while fetching area ID: {e}'
            log_error(exception)  # Log other exceptions
            raise ValueError(exception)


    def get_area_load_shedding_events(self, area_id):
        """
        Function to get load shedding events either from API or from cache.
        The result is cached for 30 minutes to reduce API calls.
        """
        # Check if we have cached data for this area ID
        if area_id in self.events_cache:
            return self.events_cache[area_id]
        
        # API call to fetch load shedding status for the given area ID
        apiURL = f'https://developer.sepush.co.za/business/2.0/area?id={area_id}'
        if self.IsDevelopmentMode:
            apiURL += '&test=future' #NOTE: For testing switch this between 'current' and 'future' to get current or future events

        try:
            response = requests.get(apiURL, headers={'Token': self.api_token})
            response.raise_for_status()  # Check for HTTP errors
            data = response.json()
        
            # Identify the current or next event
            current_event = None
            current_stage = None
        
            now = datetime.now(timezone.utc)
        
            for event in data['events']:
                event_start = datetime.fromisoformat(event['start'])
                event_end = datetime.fromisoformat(event['end'])
                
                if event_start <= now <= event_end:
                    current_event = event
                    # Use regular expression to find the stage number anywhere in the note
                    match = re.search(r'Stage (\d+)', event['note'])
                    if match:
                        current_stage = int(match.group(1))  # Extract stage number
                    break
                elif now < event_start and (current_event is None or event_start < datetime.fromisoformat(current_event['start'])):
                    current_event = event  # The next event
                    match = re.search(r'Stage (\d+)', event['note'])
                    if match:
                        current_stage = int(match.group(1))
            
            # Retrieve the schedule for the identified stage
            schedule = {}
        
            if current_stage and 'schedule' in data:
                for day in data['schedule']['days']:
                    if day['date'] == now.date().isoformat():  # Check today's schedule
                        if len(day['stages']) >= current_stage:  # Ensure the stage exists
                            stage_schedule = day['stages'][current_stage - 1]  # 0-indexed, hence `current_stage - 1`
                            if stage_schedule:
                                schedule[day['date']] = stage_schedule
            
            # Store the relevant data
            self.load_shedding_info[area_id] = {
                'current_event': current_event,
                'current_stage': current_stage,
                'today_stage_schedule': schedule
            }
        
            # Cache the load shedding info
            self.events_cache[area_id] = self.load_shedding_info[area_id]
        
            return self.load_shedding_info[area_id]

        except requests.exceptions.HTTPError as err:
            exception = f'HTTP error occurred while fetching load shedding events: {err}'
            log_error(exception)  # Log HTTP errors
            raise ValueError(exception)
        except Exception as e:
            exception = f'An error occurred while fetching load shedding events: {e}'
            log_error(exception)  # Log other exceptions
            raise ValueError(exception)

    
    def is_load_shedding_active(self, load_shedding_info):
        """
        Function to check if there is an active load shedding event.
        Returns True if a load shedding event is ongoing, False otherwise.
        """
        # Get the current time in UTC
        now_utc = datetime.now(timezone.utc)

        # Check today_stage_schedule
        today_schedule = load_shedding_info['today_stage_schedule']
        if today_schedule:
            for date, periods in today_schedule.items():
                for period in periods:
                    start_str, end_str = period.split('-')

                    # Parse the start and end times
                    start_time = datetime.strptime(f'{date} {start_str}', '%Y-%m-%d %H:%M')
                    end_time = datetime.strptime(f'{date} {end_str}', '%Y-%m-%d %H:%M')

                    # Since only current_event has timezone available
                    # I'm assuming 'today_stage_schedule' times are in the same timezone as current_event
                    if load_shedding_info['current_event']:
                        event_timezone = datetime.fromisoformat(load_shedding_info['current_event']['start']).tzinfo
                        start_time = start_time.replace(tzinfo=event_timezone)
                        end_time = end_time.replace(tzinfo=event_timezone)

                    # Convert the times to UTC for comparison
                    start_time_utc = start_time.astimezone(timezone.utc)
                    end_time_utc = end_time.astimezone(timezone.utc)

                    if start_time_utc <= now_utc <= end_time_utc:
                        return True

        # Check current_event
        current_event = load_shedding_info['current_event']
        if current_event:
            # Parse the start and end times from current_event which include timezone info
            event_start = datetime.fromisoformat(current_event['start'])
            event_end = datetime.fromisoformat(current_event['end'])

            # Compare directly as they are timezone-aware
            if event_start <= now_utc <= event_end:
                return True

        # If no active load shedding is found
        return False