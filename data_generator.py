"""
Synthetic Data Generator for Digital Pay Ops Intelligence.
Generates reproducible, realistic POS field-service and installation tickets.
All records are explicitly labeled as synthetic.
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Seed for reproducibility
RANDOM_SEED = 42

REGIONS = ["Riyadh Metro", "Jeddah Coastal", "Dammam Eastern", "Makkah Central", "Medina North"]

ISSUE_CONFIGS = {
    "New Terminal Installation": {"base_sla": 48, "weight": 0.28},
    "Hardware Malfunction": {"base_sla": 24, "weight": 0.24},
    "Network / Connectivity Offline": {"base_sla": 12, "weight": 0.22},
    "Software & Firmware Glitch": {"base_sla": 18, "weight": 0.16},
    "Paper Roll & Peripheral Setup": {"base_sla": 36, "weight": 0.10},
}

PRIORITIES = {
    "Critical": 0.15,
    "High": 0.30,
    "Medium": 0.40,
    "Low": 0.15,
}

TECHNICIANS = {
    "Riyadh Metro": ["Tariq Al-Mansoor", "Faisal Al-Harbi", "Reem Al-Otaibi", "Hassan Al-Zahrani"],
    "Jeddah Coastal": ["Omar Al-Ghamdi", "Yousef Bakhsh", "Noura Al-Saeed"],
    "Dammam Eastern": ["Khaled Al-Dossary", "Ali Al-Khaldi", "Mona Al-Qahtani"],
    "Makkah Central": ["Abdullah Hawsawi", "Ibrahim Fallatah"],
    "Medina North": ["Hamza Al-Amri", "Saud Al-Balawi"],
}


def generate_synthetic_tickets(num_tickets: int = 320, reference_time: datetime = None) -> pd.DataFrame:
    """
    Generate synthetic ticket data for POS field operations.
    
    Parameters:
    - num_tickets: Number of synthetic tickets to generate (minimum 250).
    - reference_time: Current snapshot timestamp. Defaults to 2026-10-28 16:00:00.
    """
    if reference_time is None:
        reference_time = datetime(2026, 10, 28, 16, 0, 0)

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    records = []
    issue_types = list(ISSUE_CONFIGS.keys())
    issue_weights = [ISSUE_CONFIGS[k]["weight"] for k in issue_types]

    priority_keys = list(PRIORITIES.keys())
    priority_weights = [PRIORITIES[k] for k in priority_keys]

    # Target mix:
    # ~65% Resolved (some within SLA, some breached)
    # ~35% Open/In-Progress (some within SLA, some at risk, some overdue)

    for i in range(1, num_tickets + 1):
        ticket_id = f"TICK-{1000 + i}"
        region = random.choice(REGIONS)
        issue_type = random.choices(issue_types, weights=issue_weights, k=1)[0]
        priority = random.choices(priority_keys, weights=priority_weights, k=1)[0]
        assigned_tech = random.choice(TECHNICIANS[region])

        # Adjust SLA hours slightly by priority
        base_sla = ISSUE_CONFIGS[issue_type]["base_sla"]
        if priority == "Critical":
            sla_hours = max(4, int(base_sla * 0.5))
        elif priority == "High":
            sla_hours = max(8, int(base_sla * 0.75))
        elif priority == "Low":
            sla_hours = int(base_sla * 1.5)
        else:
            sla_hours = base_sla

        # Creation time in the past 14 days
        hours_ago = random.uniform(1, 14 * 24)
        created_at = reference_time - timedelta(hours=hours_ago)
        sla_deadline = created_at + timedelta(hours=sla_hours)

        # Decide if ticket is Resolved or Open
        # Tickets older than 5 days are much more likely resolved
        is_older = (reference_time - created_at).total_seconds() / 3600 > 72
        resolved_chance = 0.85 if is_older else 0.45
        is_resolved = random.random() < resolved_chance

        if is_resolved:
            status = "Resolved"
            # Some resolved tickets breached SLA (approx 20%), others within SLA (80%)
            will_breach = random.random() < 0.22
            if will_breach:
                # Took longer than SLA
                extra_hours = random.uniform(1.0, max(4.0, sla_hours * 0.6))
                duration = sla_hours + extra_hours
            else:
                # Within SLA
                duration = random.uniform(0.5, sla_hours * 0.95)

            resolved_time = created_at + timedelta(hours=duration)
            # Ensure resolved_at does not exceed current reference time
            if resolved_time > reference_time:
                resolved_time = reference_time - timedelta(minutes=random.randint(10, 120))
            resolved_at = resolved_time
        else:
            # Unresolved tickets: either "In Progress", "Dispatched", or "Pending Merchant"
            status = random.choice(["In Progress", "Dispatched", "Pending Merchant Action"])
            resolved_at = None

        records.append({
            "ticket_id": ticket_id,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "region": region,
            "issue_type": issue_type,
            "priority": priority,
            "status": status,
            "assigned_technician": assigned_tech,
            "sla_hours": sla_hours,
            "sla_deadline": sla_deadline.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else None,
            "is_synthetic": True,
        })

    # Guarantee edge cases:
    # 1. At-risk ticket (unresolved, remaining <= 20% of SLA, not overdue)
    # 2. Overdue ticket (unresolved, deadline passed)
    # 3. Exactly on-time resolved ticket
    # 4. Breached resolved ticket
    df = pd.DataFrame(records)
    
    # Enforce specific deterministic rows for test verification
    # Row 0: Overdue open ticket
    df.loc[0, "status"] = "In Progress"
    df.loc[0, "created_at"] = (reference_time - timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[0, "sla_hours"] = 24
    df.loc[0, "sla_deadline"] = (reference_time - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[0, "resolved_at"] = None

    # Row 1: At-risk open ticket (24h SLA, 2h remaining = 8.3% remaining <= 20%)
    df.loc[1, "status"] = "Dispatched"
    df.loc[1, "created_at"] = (reference_time - timedelta(hours=22)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[1, "sla_hours"] = 24
    df.loc[1, "sla_deadline"] = (reference_time + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[1, "resolved_at"] = None

    # Row 2: Within SLA open ticket (24h SLA, 18h remaining = 75% remaining)
    df.loc[2, "status"] = "In Progress"
    df.loc[2, "created_at"] = (reference_time - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[2, "sla_hours"] = 24
    df.loc[2, "sla_deadline"] = (reference_time + timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[2, "resolved_at"] = None

    # Row 3: Within SLA resolved ticket (resolved 5h before deadline)
    df.loc[3, "status"] = "Resolved"
    df.loc[3, "created_at"] = (reference_time - timedelta(hours=40)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[3, "sla_hours"] = 24
    df.loc[3, "sla_deadline"] = (reference_time - timedelta(hours=16)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[3, "resolved_at"] = (reference_time - timedelta(hours=21)).strftime("%Y-%m-%d %H:%M:%S")

    # Row 4: Breached resolved ticket (resolved 6h after deadline)
    df.loc[4, "status"] = "Resolved"
    df.loc[4, "created_at"] = (reference_time - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[4, "sla_hours"] = 24
    df.loc[4, "sla_deadline"] = (reference_time - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    df.loc[4, "resolved_at"] = (reference_time - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")

    return df


def ensure_dataset(file_path: str = "synthetic_pos_tickets.csv", reference_time: datetime = None) -> pd.DataFrame:
    """Load existing dataset or generate new synthetic file if missing."""
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df
    df = generate_synthetic_tickets(320, reference_time=reference_time)
    df.to_csv(file_path, index=False)
    return df


if __name__ == "__main__":
    df = ensure_dataset()
    print(f"Generated {len(df)} synthetic tickets successfully.")
    print("Columns:", list(df.columns))
    print("Status counts:\n", df['status'].value_counts())
