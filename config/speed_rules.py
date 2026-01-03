# config/speed_rules.py

"""
Railway speed rules based on inferred signal aspects.

These values are HARD-CODED and must not be modified dynamically.
Any change here represents a change in railway operating rules.
"""

TRAIN_SPEED_RULES = {
    "VANDE BHARAT": {
        "SINGLE_YELLOW": 90,
        "DOUBLE_YELLOW": 110,
    },
    "COACHING": {
        "SINGLE_YELLOW": 60,
        "DOUBLE_YELLOW": 100,
    },
    "FREIGHT": {
        "SINGLE_YELLOW": 40,
        "DOUBLE_YELLOW": 55,
    },
}

ALLOWED_TRAIN_TYPES = list(TRAIN_SPEED_RULES.keys())
