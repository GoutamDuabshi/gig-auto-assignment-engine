# exploration.py - quick checks on the sample data
import pandas as pd

def load_all():
    workers = pd.read_csv('../data/workers.csv', parse_dates=['available_until'])
    profiles = pd.read_csv('../data/worker_profiles.csv')
    events = pd.read_csv('../data/events.csv', parse_dates=['event_time'])
    on_duty = pd.read_csv('../data/on_duty.csv', parse_dates=['turned_on_at'])
    return workers, profiles, events, on_duty

if __name__ == "__main__":
    w,p,e,o = load_all()
    print("Workers:", len(w))
    print("Events upcoming:", len(e[e['event_time'] > pd.Timestamp.now()]))
    print("On-duty count:", len(o))
    print(e)
