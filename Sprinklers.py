from api import System 
import numpy as np

class Sprinklers(System):
    def __init__(self, system, mode="auto"):
        self.system = system
        self.mode = mode
        self.today = self.system.TODAY
        self.season = self._get_season()
        self.water_needed_amount = self.calculate_water_needed()
        self._status = False
        self.max_base = 5

    def _get_season(self):
        date = self.today.date()
        spring = range(80, 172)  # March 21 to June 20
        summer = range(172, 264)  # June 21 to September 21
        fall = range(264, 355)
        day_of_year = date.timetuple().tm_yday

        if day_of_year in spring:
            return 1
        elif day_of_year in summer:
            return 2
        elif day_of_year in fall:
            return 3
        else:
            return 0

    def df(self):
        self.system.set_dataframe()
        return self.system.df

    def simulate(self, d):
        if self.season == 1:
            base -= 1
        elif self.season == 2:
            base -= 2
        elif self.season == 3:
            base = 1
        else:
            base -= 0
            
        today_rain = np.nan_to_num(self.system.archived_rain_tdate(d))
        yesterday_rain = np.nan_to_num(self.system.archived_rain_ydate(d))
        tomorrow_rain = np.nan_to_num(self.system.archived_rain_tmdate(d))

        
        # Subtract today_data from the base
        base -= today_rain 
        
        # Subtract half of yesterday_data from the base
        base -= (yesterday_rain / 2)

        base -= (tomorrow_rain / 3)

        action = True if base > 0 else False
        
        if action:
            convert = base / 40
            duration = 3_600_000 * convert  # grass needs 50mm - 50mm = 1 hour of sprinklers
        else:
            duration = 0
        return {"action": bool(action), "duration": float(duration)}


    def get_status(self):
        return self._status
    
    def set_status(self, status):
        self._status = status

    def set_mode(self, mode):
        self.mode = mode
    
    def get_mode(self):
        return self.mode
    
    def get_today_forecast_rain(self):
        return self.system.today_forecast_rain()
    
    def get_yesterday_rain(self):
        return self.system.yesterday_rain()  
    
    def get_today_historical_rain(self):
        return self.system.today_historical_rain()
    
    def get_tomorrow_forecast_rain(self):
        return self.system.tomorrow_forecast_rain()  
    
    def calculate_water_needed(self):
        base=5
        # base water based on season
        if self.season == 1:
            base -= 1
        elif self.season == 2:
            base -= 2
        elif self.season == 3:
            base = 1
        else:
            base -= 0

        today_rain = np.nan_to_num(self.get_today_forecast_rain())
        yesterday_rain = np.nan_to_num(self.get_yesterday_rain())
        tomorrow_rain = np.nan_to_num(self.get_tomorrow_forecast_rain())
        
        # Subtract today_data from the base
        base -= today_rain 
        
        # Subtract half of yesterday_data from the base
        base -= (yesterday_rain / 2)

        base -= (tomorrow_rain / 3)
        
        return max(base, 0)
    
    def update_water_needed(self):
        self.water_needed_amount = self.calculate_water_needed()
    
    def _action(self):
        return self.water_needed_amount > 0
    
    def message(self):
        print(self.water_needed_amount)
        if self.water_needed_amount > 0:
            convert = self.water_needed_amount / self.max_base
            duration = 3_600_000 * convert  # grass needs 50mm - 50mm = 1 hour of sprinklers
        else:
            duration = 0
        if duration < 60_000:
            duration = 0
        action = self._action()
        return {"action": bool(action), "duration": float(duration)}

