# utils.py - helper functions (distance, normalizers)

import math
import pandas as pd

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    return 2 * R * math.asin(math.sqrt(a))

def normalize_series(s):
    # simple min-max normalize, handle constant series
    if s.max() == s.min():
        return s.apply(lambda x: 0.5)
    return (s - s.min()) / (s.max() - s.min())

def within_time_cutoff(event_time, cutoff_hours=6):
    # return latest allowed acceptance timestamp
    return event_time - pd.Timedelta(hours=cutoff_hours)
