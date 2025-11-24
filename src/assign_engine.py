# assign_engine.py
# Core assignment logic:
# - For each unfilled event, score available workers by distance, rating, availability, and criteria match (if applicable).
# - Equal weighting among normalized distance_score, rating_score, availability_score.
# - For criteria-based events, profile match multiplies final score.
# - Only assign if worker can accept before cutoff (6 hours before event_time).
# - If assigned workers >= total_slots then cancel remaining assignments for event.

import pandas as pd
import json
import os
from datetime import datetime
from utils import haversine_km, normalize_series, within_time_cutoff
from criteria_matcher import match_score

ASSIGNMENTS_OUT = '../data/assignments_out.csv'

def load_data():
    workers = pd.read_csv('../data/workers.csv', parse_dates=['available_until'])
    profiles = pd.read_csv('../data/worker_profiles.csv')
    events = pd.read_csv('../data/events.csv', parse_dates=['event_time'])
    on_duty = pd.read_csv('../data/on_duty.csv', parse_dates=['turned_on_at'])
    return workers, profiles, events, on_duty

def score_workers_for_event(event, workers_df, profiles_df, on_duty_df, max_distance_km=10):
    # event: Series
    # compute distance to each worker, only consider is_active ==1 and available_until >= cutoff
    cutoff_ts = within_time_cutoff(event['event_time'], cutoff_hours=6)
    eligible = workers_df[
        (workers_df['is_active'] == 1) &
        (workers_df['available_until'] >= cutoff_ts)
    ].copy()

    # distance
    eligible['distance_km'] = eligible.apply(lambda r: haversine_km(event['lat'], event['lon'], r['lat'], r['lon']), axis=1)
    # restrict to those within max_distance_km for initial assignment preference
    eligible = eligible[eligible['distance_km'] <= max_distance_km]
    if eligible.empty:
        return pd.DataFrame()

    # Normalize distance (lower is better -> invert)
    eligible['dist_norm'] = 1 - normalize_series(eligible['distance_km'])
    # rating normalize
    eligible['rating_norm'] = normalize_series(eligible['rating'])
    # availability score: 1 if available_until is long (normalize on epoch seconds)
    eligible['avail_seconds'] = eligible['available_until'].astype('int64') // 10**9
    eligible['avail_norm'] = normalize_series(eligible['avail_seconds'])

    # equal weights among distance, rating, availability
    eligible['base_score'] = (eligible['dist_norm'] + eligible['rating_norm'] + eligible['avail_norm']) / 3.0

    # if criteria-based, apply profile match multiplier
    if event.get('criteria_based', 0) in [1, '1', True]:
        crit = event.get('criteria_json', '{}')
        eligible['criteria_match'] = eligible['worker_id'].apply(lambda wid: match_score(wid, crit, profiles_df))
        # Multiply base_score by (0.5 + 0.5*criteria_match) so match helps but doesn't totally dominate
        eligible['final_score'] = eligible['base_score'] * (0.5 + 0.5 * eligible['criteria_match'])
    else:
        eligible['criteria_match'] = 1.0
        eligible['final_score'] = eligible['base_score']

    # sort by final_score desc
    eligible = eligible.sort_values('final_score', ascending=False)
    return eligible

def assign_for_event(event_id, max_assign=5):
    workers, profiles, events, on_duty = load_data()
    event = events[events['event_id'] == event_id].iloc[0]
    remaining_slots = int(event['total_slots'] - event['filled_slots'])
    if remaining_slots <= 0 or event['event_time'] < pd.Timestamp.now():
        print("No slots to fill or event passed.")
        return

    scored = score_workers_for_event(event, workers, profiles, on_duty, max_distance_km=5)
    if scored.empty:
        # if none found, fallback to on-duty search ignoring 'is_active' but within radius
        print("No active workers within radius; checking on-duty pool")
        on_duty_workers = on_duty.copy()
        on_duty_workers['distance_km'] = on_duty_workers.apply(lambda r: haversine_km(event['lat'], event['lon'], r['lat'], r['lon']), axis=1)
        on_duty_workers = on_duty_workers[on_duty_workers['distance_km'] <= 5]
        if on_duty_workers.empty:
            print("No on-duty workers nearby.")
            return
        scored = on_duty_workers.rename(columns={'turned_on_at':'available_until'})
        # minimal score calculation
        scored['final_score'] = 0.5  # baseline for on-duty fallback

    # Now iterate and produce assignments up to remaining_slots
    assigned = []
    for i, row in scored.iterrows():
        if remaining_slots <= 0:
            break
        wid = row['worker_id']
        # double-check worker not already assigned to this event (in real db we'd check)
        assigned.append({'event_id': event_id, 'worker_id': wid, 'assigned_at': datetime.utcnow().isoformat(), 'score': float(row.get('final_score', 0))})
        remaining_slots -= 1

    # Save assignments to CSV (append)
    out_df = pd.DataFrame(assigned)
    if os.path.exists(ASSIGNMENTS_OUT):
        prev = pd.read_csv(ASSIGNMENTS_OUT)
        out_df = pd.concat([prev, out_df], ignore_index=True)
    out_df.to_csv(ASSIGNMENTS_OUT, index=False)
    print(f"Assigned {len(assigned)} workers to event {event_id}. Saved to {ASSIGNMENTS_OUT}")

    # After assignment, if filled then mark event as closed in events.csv (simple file write)
    # (In a production DB this would be transactional)
    if remaining_slots <= 0:
        events.loc[events['event_id'] == event_id, 'filled_slots'] = events.loc[events['event_id'] == event_id, 'total_slots']
        events.loc[events['event_id'] == event_id, 'status'] = 'closed'
        events.to_csv('../data/events.csv', index=False)
        print(f"Event {event_id} is now full. Updated events.csv and set status closed.")

if __name__ == "__main__":
    # Example usage
    assign_for_event('E002')
