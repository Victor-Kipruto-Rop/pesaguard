"""
Central place to define Kafka topic names so producer/consumer
code never hardcodes strings inconsistently.
"""

TRANSACTIONS_RAW = "mpesa.transactions.raw"
TRANSACTIONS_MATCHED = "mpesa.transactions.matched"
DISCREPANCIES = "mpesa.discrepancies"

ALL_TOPICS = [TRANSACTIONS_RAW, TRANSACTIONS_MATCHED, DISCREPANCIES]
