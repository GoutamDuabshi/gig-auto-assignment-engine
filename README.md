# gig-auto-assignment-engine
Automatic assignment of gigs

Gig Auto-Assignment Engine (DailyGo)

Purpose
-------
Automatically allocate workers to gigs using a balanced scoring system that
considers distance, badge rating, and worker availability. Supports two event
types:
  - criteria-based: event manager specifies minimum profile thresholds
  - non-criteria-based: regular auto-assignment

Key rules implemented
---------------------
- Equal weighting: distance, rating and availability are normalized and averaged.
- Area mapping: Haversine formula to compute geographic distance.
- Criteria-based flow: when an event has criteria, the worker's profile is checked
  (experience_score, skill_score, past acceptance rate) and used to boost the final score.
- Acceptance cutoff: workers must be available to accept up to 6 hours before event_time.
- Fallback: if no active workers are found nearby, use the on-duty pool (workers who turned on On-Duty).
- Cancellation: if the event fills (filled_slots == total_slots) the event is set to 'closed' and pending assignments are ignored.

How to run
----------
1. Populate `data/` with actual CSVs or use the provided samples.
2. Quick EDA: `python src/exploration.py`
3. Run assignment for an event: `python src/assign_engine.py`
   - The script will call `assign_for_event('E002')` by default (edit event id as required).

Notes
-----
- This repo models the real DailyGo approach. It is intentionally simple and readable.
- In production, swap CSVs for a transactional DB, add retries/locks, and use push-notification service for worker notifications.
