#Завдання 09.3.3-1 .
#Імпортування модулів.
from pyowm import OWM
#Айпі ключ.
API_KEY = "ef2206ff5da67de63306d0b143e20872"
# ---------- FREE API KEY examples --------------------- .
#Ініціалізація OWM з API-ключем.
owm = OWM (API_KEY)
mgr = owm.weather_manager()
#Search for current weather in London (Great Britain) and get details.
observation = mgr.weather_at_place ("London,GB")
w = observation.weather
#Деф для виводу деталей погоди.
def get_weather():
    print (w.detailed_status)         # "clouds"
    print (w.wind())                  # {"speed": 4.6, "deg": 330}
    print (w.humidity)                # 87
    print (w.temperature ("celsius"))  # {"temp_max": 10.5, "temp": 9.7, "temp_min": 9.0}
    print (w.rain)                    # {}
    print (w.heat_index)              # None
    print (w.clouds)                  # 75
#.
