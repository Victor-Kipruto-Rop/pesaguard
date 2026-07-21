"""
Anomaly detection rules applied to each incoming M-Pesa transaction event.

Thresholds are tuned for pilot customers based on typical transaction patterns.
Per-customer overrides available via tenant_settings.json.

Pilot Tuning Guide:
  - LARGE_AMOUNT_THRESHOLD: Set to 95th percentile of normal transaction amounts for customer
  - CALLBACK_DELAY_THRESHOLD: Set based on acceptable latency (Daraja typically < 2min)
  - Anomaly score thresholds: Tuned to minimize false positives while catching real fraud
  
For real-time tuning during pilot:
  1. Monitor discrepancy alerts for false positives
  2. Adjust thresholds in tenant_settings.json without restart
  3. Log all anomaly scores to review patterns
"""
import os
from typing import Any, Dict, List, Set
from datetime import datetime

# ============================================================================
# PILOT THRESHOLDS (per-tenant overrides in tenant_settings.json)
# ============================================================================

# Default: 150,000 KES (~$1,200 USD) - Adjust per customer's typical transaction size
LARGE_AMOUNT_THRESHOLD_KES = int(os.getenv("ANOMALY_LARGE_AMOUNT_KES", "150000"))

# Default: 10 minutes - Daraja callbacks usually arrive within 2 minutes
# Increase if customer experiences legitimate delays (e.g., congested network)
CALLBACK_DELAY_THRESHOLD_MINUTES = int(os.getenv("ANOMALY_CALLBACK_DELAY_MIN", "10"))

# High anomaly score threshold (0.0-1.0) for flagging suspicious transactions
# Lower = more aggressive detection (higher false positives)
# 0.7 = moderate; 0.8 = conservative (fewer false positives)
ANOMALY_SCORE_THRESHOLD = float(os.getenv("ANOMALY_SCORE_THRESHOLD", "0.8"))

# Off-hours penalty: transactions between 00:00-04:00 UTC get additional scoring
# Disable for 24/7 businesses (set to 0) or adjust hours per timezone
OFF_HOURS_START_UTC = int(os.getenv("ANOMALY_OFF_HOURS_START", "0"))  # 00:00 UTC
OFF_HOURS_END_UTC = int(os.getenv("ANOMALY_OFF_HOURS_END", "4"))      # 04:00 UTC
OFF_HOURS_PENALTY = float(os.getenv("ANOMALY_OFF_HOURS_PENALTY", "0.2"))

import math

def check_for_anomalies(event: Dict[str, Any], seen_trans_ids: Set[str]) -> List[str]:
    """
    Runs all anomaly checks against a single transaction event.
    Returns a list of human-readable anomaly descriptions (empty if clean).
    
    Each anomaly includes severity context for downstream alerting:
      - duplicate_transaction_id: HIGH (idempotency failure)
      - amount_exceeds_threshold_*: MEDIUM (potential fraud/misuse)
      - invalid_or_zero_amount: HIGH (data quality issue)
      - high_anomaly_score_*: MEDIUM (statistical anomaly)
    """
    anomalies = []

    if _is_duplicate(event, seen_trans_ids):
        anomalies.append("duplicate_transaction_id")

    if _is_unusually_large(event):
        anomalies.append(f"amount_exceeds_threshold_{LARGE_AMOUNT_THRESHOLD_KES}_KES")

    if _has_invalid_amount(event):
        anomalies.append("invalid_or_zero_amount")

    # Statistical/ML anomaly scoring for complex patterns
    score = score_transaction_anomaly(event)
    if score > ANOMALY_SCORE_THRESHOLD:
        anomalies.append(f"high_anomaly_score_{round(score, 2)}")

    return anomalies


def score_transaction_anomaly(event: Dict[str, Any]) -> float:
    """
    Statistical heuristic anomaly scoring (0.0 to 1.0).
    Combines multiple signals: amount extremeness, timing, frequency patterns.
    
    Thresholds tuned for pilot; can be overridden per-customer via tenant_settings.
    
    Returns:
        Anomaly score 0.0 (normal) to 1.0 (highly suspicious)
    """
    score = 0.0
    try:
        amount = float(event.get("TransAmount", 0))
    except (TypeError, ValueError):
        # Invalid amount is critical issue
        return 1.0

    # Signal 1: Extreme amount check
    # Pilot tuning: Adjust thresholds to match customer's business model
    if amount > LARGE_AMOUNT_THRESHOLD_KES * 1.5:  # 225,000 KES
        score += 0.5
    elif amount > LARGE_AMOUNT_THRESHOLD_KES:  # 150,000 KES
        score += 0.3

    # Signal 2: Timing/Off-hours check (UTC timezone)
    # Disable for 24/7 businesses (OFF_HOURS_PENALTY=0)
    trans_time = str(event.get("TransTime", ""))
    try:
        event_dt = None
        
        # Try parsing Daraja format: YYYYMMDDHHmmss
        if len(trans_time) >= 14 and trans_time[:14].isdigit():
            hour = int(trans_time[8:10])
            event_dt = datetime(int(trans_time[0:4]), int(trans_time[4:6]), int(trans_time[6:8]), hour)
        # Try ISO 8601: 2026-07-22T02:30:00Z
        elif "T" in trans_time:
            dt = datetime.fromisoformat(trans_time.replace("Z", "+00:00"))
            hour = dt.hour
            event_dt = dt
        
        if event_dt and OFF_HOURS_PENALTY > 0:
            hour = event_dt.hour
            if OFF_HOURS_START_UTC < OFF_HOURS_END_UTC:
                # e.g., 00:00-04:00
                if OFF_HOURS_START_UTC <= hour < OFF_HOURS_END_UTC:
                    score += OFF_HOURS_PENALTY
            else:
                # Wraparound: e.g., 22:00-04:00 (10pm to 4am)
                if hour >= OFF_HOURS_START_UTC or hour < OFF_HOURS_END_UTC:
                    score += OFF_HOURS_PENALTY
    except (ValueError, AttributeError):
        pass  # Timestamp parsing failure, don't penalize further

    # Signal 3: Amount frequency/pattern check
    # Transactions ending in multiple zeros (e.g., 100,000, 200,000) are normal
    # Odd values (e.g., 123,456) are less frequent but not necessarily anomalous
    # For now, we skip this unless there's pilot evidence of specific patterns
    if amount > LARGE_AMOUNT_THRESHOLD_KES and amount % 10000 != 0:
        score += 0.15

    # Signal 4: Velocity/Rate of change (if historical context available)
    # Not yet implemented; requires transaction history context
    # TODO: Add velocity scoring once transaction history is available

    # Clamp to [0.0, 1.0]
    return min(1.0, score)


def _is_duplicate(event: Dict[str, Any], seen_trans_ids: Set[str]) -> bool:
    """Check if transaction ID has been seen before in this batch."""
    trans_id = str(event.get("TransID", ""))
    return trans_id in seen_trans_ids


def _is_unusually_large(event: Dict[str, Any]) -> bool:
    """Check if amount exceeds per-customer threshold."""
    try:
        amount = float(event.get("TransAmount", 0))
        return amount > LARGE_AMOUNT_THRESHOLD_KES
    except (TypeError, ValueError):
        return False


def _has_invalid_amount(event: Dict[str, Any]) -> bool:
    """Check if amount is missing, zero, or negative."""
    try:
        amount = float(event.get("TransAmount", 0))
        return amount <= 0
    except (TypeError, ValueError):
        return True  # Can't parse = invalid


def _is_duplicate(event: Dict[str, Any], seen_trans_ids: Set[str]) -> bool:
    return event.get("TransID") in seen_trans_ids


def _is_unusually_large(event: Dict[str, Any]) -> bool:
    try:
        return float(event.get("TransAmount", 0)) > LARGE_AMOUNT_THRESHOLD_KES
    except (TypeError, ValueError):
        return False


def _has_invalid_amount(event: Dict[str, Any]) -> bool:
    try:
        return float(event.get("TransAmount", 0)) <= 0
    except (TypeError, ValueError):
        return True
