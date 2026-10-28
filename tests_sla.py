"""
Unit tests for SLA Engine and Metrics Calculation in Digital Pay Ops Intelligence.
Tests SLA risk classification, edge cases, denominator handling, and KPI accuracy.
"""

import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from sla_engine import (
    classify_ticket_sla,
    enrich_ticket_data,
    calculate_executive_kpis,
    calculate_regional_summary,
    SLA_OVERDUE,
    SLA_AT_RISK,
    SLA_WITHIN_SLA,
    SLA_BREACHED,
)


class TestSLAEngine(unittest.TestCase):

    def setUp(self):
        self.ref_time = datetime(2026, 10, 28, 16, 0, 0)

    def test_overdue_classification(self):
        # Unresolved ticket whose SLA deadline has passed
        row = pd.Series({
            "status": "In Progress",
            "created_at": self.ref_time - timedelta(hours=30),
            "sla_deadline": self.ref_time - timedelta(hours=6),
            "sla_hours": 24,
            "resolved_at": None,
        })
        status, delta = classify_ticket_sla(row, self.ref_time)
        self.assertEqual(status, SLA_OVERDUE)
        self.assertLess(delta, 0)

    def test_at_risk_classification(self):
        # Unresolved ticket with 20% or less of allocated SLA time remaining
        # e.g., 24h SLA, created 22h ago, deadline is in 2h (2h/24h = 8.33% <= 20%)
        row = pd.Series({
            "status": "Dispatched",
            "created_at": self.ref_time - timedelta(hours=22),
            "sla_deadline": self.ref_time + timedelta(hours=2),
            "sla_hours": 24,
            "resolved_at": None,
        })
        status, delta = classify_ticket_sla(row, self.ref_time)
        self.assertEqual(status, SLA_AT_RISK)
        self.assertGreater(delta, 0)
        self.assertLessEqual(delta, 24 * 0.20)

    def test_within_sla_unresolved(self):
        # Unresolved ticket with plenty of time remaining (> 20%)
        # e.g., 24h SLA, created 4h ago, deadline in 20h (20h/24h = 83.3% > 20%)
        row = pd.Series({
            "status": "In Progress",
            "created_at": self.ref_time - timedelta(hours=4),
            "sla_deadline": self.ref_time + timedelta(hours=20),
            "sla_hours": 24,
            "resolved_at": None,
        })
        status, delta = classify_ticket_sla(row, self.ref_time)
        self.assertEqual(status, SLA_WITHIN_SLA)
        self.assertGreater(delta, 24 * 0.20)

    def test_within_sla_resolved(self):
        # Resolved ticket completed on or before deadline
        row = pd.Series({
            "status": "Resolved",
            "created_at": self.ref_time - timedelta(hours=20),
            "sla_deadline": self.ref_time - timedelta(hours=4),
            "sla_hours": 16,
            "resolved_at": self.ref_time - timedelta(hours=8),  # 4h before deadline
        })
        status, delta = classify_ticket_sla(row, self.ref_time)
        self.assertEqual(status, SLA_WITHIN_SLA)
        self.assertGreaterEqual(delta, 0)

    def test_breached_resolved(self):
        # Resolved ticket completed after deadline
        row = pd.Series({
            "status": "Resolved",
            "created_at": self.ref_time - timedelta(hours=30),
            "sla_deadline": self.ref_time - timedelta(hours=10),
            "sla_hours": 20,
            "resolved_at": self.ref_time - timedelta(hours=5),  # 5h after deadline
        })
        status, delta = classify_ticket_sla(row, self.ref_time)
        self.assertEqual(status, SLA_BREACHED)
        self.assertLess(delta, 0)

    def test_edge_case_zero_remaining_time(self):
        # Unresolved ticket at exact moment of deadline
        row = pd.Series({
            "status": "In Progress",
            "created_at": self.ref_time - timedelta(hours=24),
            "sla_deadline": self.ref_time,
            "sla_hours": 24,
            "resolved_at": None,
        })
        status, delta = classify_ticket_sla(row, self.ref_time)
        # At delta=0, remaining_ratio = 0 <= 0.20, so it's At Risk
        self.assertEqual(status, SLA_AT_RISK)

    def test_safe_zero_denominator_kpis(self):
        # If no tickets are resolved, SLA compliance must not raise ZeroDivisionError
        data = pd.DataFrame([
            {
                "ticket_id": "T-1",
                "created_at": self.ref_time - timedelta(hours=2),
                "sla_deadline": self.ref_time + timedelta(hours=10),
                "sla_hours": 12,
                "status": "In Progress",
                "resolved_at": None,
                "region": "Riyadh Metro",
            }
        ])
        enriched = enrich_ticket_data(data, self.ref_time)
        kpis = calculate_executive_kpis(enriched)
        self.assertEqual(kpis["resolved_tickets"], 0)
        self.assertEqual(kpis["open_tickets"], 1)
        self.assertIn("sla_compliance_pct", kpis)
        self.assertEqual(kpis["high_risk_overdue"], 0)

    def test_kpi_calculations_and_exact_denominator(self):
        # 4 tickets:
        # Ticket 1: Resolved within SLA
        # Ticket 2: Resolved breached
        # Ticket 3: Open within SLA
        # Ticket 4: Open overdue
        data = pd.DataFrame([
            {
                "ticket_id": "T-1",
                "created_at": self.ref_time - timedelta(hours=10),
                "sla_deadline": self.ref_time - timedelta(hours=2),
                "sla_hours": 8,
                "status": "Resolved",
                "resolved_at": self.ref_time - timedelta(hours=4),
                "region": "Riyadh Metro",
            },
            {
                "ticket_id": "T-2",
                "created_at": self.ref_time - timedelta(hours=20),
                "sla_deadline": self.ref_time - timedelta(hours=12),
                "sla_hours": 8,
                "status": "Resolved",
                "resolved_at": self.ref_time - timedelta(hours=6),
                "region": "Riyadh Metro",
            },
            {
                "ticket_id": "T-3",
                "created_at": self.ref_time - timedelta(hours=2),
                "sla_deadline": self.ref_time + timedelta(hours=10),
                "sla_hours": 12,
                "status": "In Progress",
                "resolved_at": None,
                "region": "Riyadh Metro",
            },
            {
                "ticket_id": "T-4",
                "created_at": self.ref_time - timedelta(hours=20),
                "sla_deadline": self.ref_time - timedelta(hours=8),
                "sla_hours": 12,
                "status": "In Progress",
                "resolved_at": None,
                "region": "Riyadh Metro",
            },
        ])
        enriched = enrich_ticket_data(data, self.ref_time)
        kpis = calculate_executive_kpis(enriched)

        # Denominator should be 2 resolved tickets
        self.assertEqual(kpis["total_tickets"], 4)
        self.assertEqual(kpis["open_tickets"], 2)
        self.assertEqual(kpis["resolved_tickets"], 2)
        self.assertEqual(kpis["resolved_within_sla"], 1)
        # Compliance = 1 / 2 = 50.0%
        self.assertEqual(kpis["sla_compliance_pct"], 50.0)
        self.assertEqual(kpis["high_risk_overdue"], 1)
        self.assertEqual(kpis["breached_count"], 1)

    def test_regional_summary(self):
        data = pd.DataFrame([
            {
                "ticket_id": "T-1",
                "region": "Riyadh Metro",
                "created_at": self.ref_time - timedelta(hours=10),
                "sla_deadline": self.ref_time - timedelta(hours=2),
                "sla_hours": 8,
                "status": "Resolved",
                "resolved_at": self.ref_time - timedelta(hours=4),
            },
            {
                "ticket_id": "T-2",
                "region": "Jeddah Coastal",
                "created_at": self.ref_time - timedelta(hours=20),
                "sla_deadline": self.ref_time - timedelta(hours=12),
                "sla_hours": 8,
                "status": "Resolved",
                "resolved_at": self.ref_time - timedelta(hours=6),
            },
        ])
        enriched = enrich_ticket_data(data, self.ref_time)
        reg_summary = calculate_regional_summary(enriched)
        self.assertEqual(len(reg_summary), 2)
        riyadh = reg_summary[reg_summary["Region"] == "Riyadh Metro"].iloc[0]
        self.assertEqual(riyadh["SLA Compliance (%)"], 100.0)
        jeddah = reg_summary[reg_summary["Region"] == "Jeddah Coastal"].iloc[0]
        self.assertEqual(jeddah["SLA Compliance (%)"], 0.0)


if __name__ == "__main__":
    unittest.main()
