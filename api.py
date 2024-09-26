import openmeteo_requests
import numpy as np
import pandas as pd
import requests_cache
import datetime
from retry_requests import retry

pd.set_option('display.max_rows', None)

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

class WeatherPointArchived:
    def __init__(self, date, precipitation, rain):
        self.date = date
        self.precipitation = precipitation
        self.rain = rain

class WeatherPointHistory:
    def __init__(self, date, precipitation, rain):
        self.date = date
        self.precipitation = precipitation
        self.rain = rain

class WeatherPointForecast:
    def __init__(self, date, precipitation, rain, showers):
        self.date = date
        self.precipitation = precipitation
        self.rain = rain
        self.showers = showers

class WeatherReport:
    def __init__(self, archived_data, historical_data, forecast_data):
        self.archived_points = [WeatherPointHistory(*point) for point in archived_data]
        self.historical_points = [WeatherPointHistory(*point) for point in historical_data]
        self.forecast_points = [WeatherPointForecast(*point) for point in forecast_data]


    def __repr__(self):
        return f"WeatherReport with {len(self.archived_points)} archived points, {len(self.historical_points)} historical points, and {len(self.forecast_points)} forecast points"

    def __getitem__(self, index):
        total_points = len(self.archived_points) + len(self.historical_points) + len(self.forecast_points)
        if index < len(self.archived_points):
            return self.archived_points[index]
        elif index < len(self.archived_points) + len(self.historical_points):
            return self.historical_points[index - len(self.archived_points)]
        elif index < total_points:
            return self.forecast_points[index - len(self.archived_points) - len(self.historical_points)]
        else:
            raise IndexError("Index out of range")


def make_api_requests(TODAY, LAST_WEEK):
	url_archived = "https://archive-api.open-meteo.com/v1/archive"
	params_historical = {
		"latitude": 26.658010,
		"longitude": -80.062670,
		"start_date": LAST_WEEK.strftime('%Y-%m-%d'),
		"end_date": TODAY.strftime('%Y-%m-%d'),
		"hourly": ["precipitation", "rain"]
	}
	responses_archived = openmeteo.weather_api(url_archived, params=params_historical)

	url_historical = "https://historical-forecast-api.open-meteo.com/v1/forecast"
	responses_historical = openmeteo.weather_api(url_historical, params=params_historical)

	# Forecast data request
	url_forecast = "https://api.open-meteo.com/v1/forecast"
	params_forecast = {
		"latitude": 26.658010,
		"longitude": -80.062670,
		"hourly": ["precipitation", "rain", "showers"],
		"forecast_days": 7
	}
	responses_forecast = openmeteo.weather_api(url_forecast, params=params_forecast)
    
	response_archived = responses_archived[0]
	hourly_archived = response_archived.Hourly()
	hourly_precipitation_archived = hourly_archived.Variables(0).ValuesAsNumpy()
	hourly_rain_archived = hourly_archived.Variables(1).ValuesAsNumpy()

	start_time_archived = datetime.datetime.utcfromtimestamp(hourly_archived.Time())
	time_interval = datetime.timedelta(seconds=hourly_archived.Interval())
	num_steps_archived = len(hourly_precipitation_archived)
	hourly_dates_archived = np.array([start_time_archived + i * time_interval for i in range(num_steps_archived)])

	# Process historical hourly data
	response_historical = responses_historical[0]
	hourly_historical = response_historical.Hourly()
	hourly_precipitation_historical = hourly_historical.Variables(0).ValuesAsNumpy()
	hourly_rain_historical = hourly_historical.Variables(1).ValuesAsNumpy()

	start_time_historical = datetime.datetime.utcfromtimestamp(hourly_historical.Time())
	time_interval = datetime.timedelta(seconds=hourly_historical.Interval())
	num_steps_historical = len(hourly_precipitation_historical)
	hourly_dates_historical = np.array([start_time_historical + i * time_interval for i in range(num_steps_historical)])

	# Process forecast hourly data
	response_forecast = responses_forecast[0]
	hourly_forecast = response_forecast.Hourly()
	hourly_precipitation_forecast = hourly_forecast.Variables(0).ValuesAsNumpy()
	hourly_rain_forecast = hourly_forecast.Variables(1).ValuesAsNumpy()
	hourly_showers_forecast = hourly_forecast.Variables(2).ValuesAsNumpy()

	start_time_forecast = datetime.datetime.utcfromtimestamp(hourly_forecast.Time())
	num_steps_forecast = len(hourly_precipitation_forecast)
	hourly_dates_forecast = np.array([start_time_forecast + i * time_interval for i in range(num_steps_forecast)])

	# Combine all data and create WeatherReport
	hourly_data_archived = np.array(list(zip(hourly_dates_archived, hourly_precipitation_archived, hourly_rain_archived)))
	hourly_data_historical = np.array(list(zip(hourly_dates_historical, hourly_precipitation_historical, hourly_rain_historical)))
	hourly_data_forecast = np.array(list(zip(hourly_dates_forecast, hourly_precipitation_forecast, hourly_rain_forecast, hourly_showers_forecast)))
	weather_report = WeatherReport(hourly_data_archived, hourly_data_historical, hourly_data_forecast)
	return weather_report




# Update System class
class System:
    def __init__(self, TODAY, LAST_WEEK):
        self.TODAY = TODAY
        self.weather_report = make_api_requests(TODAY, LAST_WEEK)
        self.df = None
        

    def yesterday_rain(self):
        yesterday = self.TODAY.date() - datetime.timedelta(days=1)
        yesterday_precipitation = sum(
            point.precipitation
            for point in self.weather_report.historical_points
            if point.date.date() == yesterday
        )
        return yesterday_precipitation
        
    
    def archived_rain_tdate(self, date):
          print(date)
        #   print([point.precipitation
		# 	for point in self.weather_report.archived_points
		# 	if point.date.date() == date.date()])
          archived_date_precipitation = sum(
			point.precipitation
			for point in self.weather_report.archived_points
			if point.date.date() == date.date()
		)
          print(archived_date_precipitation)
          return archived_date_precipitation
    
    def archived_rain_ydate(self, date):
          archived_date_precipitation = sum(
			point.precipitation
			for point in self.weather_report.archived_points
			if point.date.date() == (date - datetime.timedelta(days=1)).date()
		)
          return archived_date_precipitation
    
    def archived_rain_tmdate(self, date):
          archived_date_precipitation = sum(
			point.precipitation
			for point in self.weather_report.archived_points
			if point.date.date() == (date + datetime.timedelta(days=1)).date()
		)
          return archived_date_precipitation
    
    def today_forecast_rain(self):
        now = self.TODAY
        today_precipitation = sum(
            point.precipitation 
            for point in self.weather_report.forecast_points 
            if point.date.replace(tzinfo=datetime.timezone.utc).date() == now.date()
            and point.date.replace(tzinfo=datetime.timezone.utc) > now
        )
        return today_precipitation
    
    def today_historical_rain(self):
        today = self.TODAY.date()
        today_precipitation = sum(
            point.precipitation 
            for point in self.weather_report.historical_points 
            if point.date.replace(tzinfo=datetime.timezone.utc).date() == today
            and not np.isnan(point.precipitation)
        )
        return today_precipitation
    def tomorrow_forecast_rain(self):
        tomorrow = self.TODAY.date() + datetime.timedelta(days=1)
        tomorrow_precipitation = sum(
            point.precipitation
            for point in self.weather_report.forecast_points
            if point.date.replace(tzinfo=datetime.timezone.utc).date() == tomorrow
        )
        return tomorrow_precipitation

    def create_dataframe(self):
        data = []
        
        # Add archived data
        for point in self.weather_report.archived_points:
            data.append({
                'date': point.date,
                'precipitation': point.precipitation,
                'rain': point.rain,
                'showers': None,
                'data_type': 'archived'
            })
        
        # Add historical data
        for point in self.weather_report.historical_points:
            data.append({
                'date': point.date,
                'precipitation': point.precipitation,
                'rain': point.rain,
                'showers': None,
                'data_type': 'historical'
            })
        
        # Add forecast data
        for point in self.weather_report.forecast_points:
            data.append({
                'date': point.date,
                'precipitation': point.precipitation,
                'rain': point.rain,
                'showers': point.showers,
                'data_type': 'forecast'
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        return df
    def set_dataframe(self):
	    self.df = self.create_dataframe()

