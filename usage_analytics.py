
from collections import defaultdict

usage = defaultdict(int)

def track(event):
    usage[event] += 1

def get_usage_summary():
    return dict(usage)

def export_usage_report():
    for k, v in get_usage_summary().items():
        print(f"{k}: {v}")
