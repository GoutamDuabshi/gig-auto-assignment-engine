# criteria_matcher.py
# For criteria-based events, compute a profile match score using worker_profiles

import json
import pandas as pd

def match_score(worker_id, criteria_json, profiles_df):
    # criteria_json: dict with thresholds, e.g., {"min_experience":0.7,...}
    c = json.loads(criteria_json) if isinstance(criteria_json, str) else c = criteria_json
    # Get worker row
    row = profiles_df[profiles_df['worker_id'] == worker_id]
    if row.empty:
        return 0.0
    row = row.iloc[0]
    score = 0.0
    weight_sum = 0.0
    # Example: compare experience_score with min_experience
    if 'min_experience' in c:
        weight_sum += 1.0
        score += (row['experience_score'] >= c['min_experience']) * 1.0
    if 'skill_required' in c:
        weight_sum += 1.0
        score += (row['skill_score'] >= c['skill_required']) * 1.0
    # fallback: if no criteria, return average of profile metrics
    if weight_sum == 0:
        return (row['experience_score'] + row['skill_score']) / 2.0
    return score / weight_sum
