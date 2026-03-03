"""
mock_data.py — AskOps by RaveMinds
====================================
5 trade scenarios × 6 sources:
  Oracle, Datadog Alerts, Datadog Logs, Datadog APM,
  App Events, Kafka, EKS, Manager Summary
"""

ORACLE_TRADES = {
    "12345": {
        "trade_id": "12345", "instrument": "AAPL", "direction": "BUY",
        "quantity": 5000, "price": 187.42, "trader": "john.smith@firm.com",
        "status": "FAILED", "sla_breach": True,
        "lifecycle": [
            {"state": "RECEIVED",  "timestamp": "2024-01-15 09:47:00", "note": "Trade received from OMS"},
            {"state": "VALIDATED", "timestamp": "2024-01-15 09:47:02", "note": "Passed pre-trade risk checks"},
            {"state": "ROUTED",    "timestamp": "2024-01-15 09:47:05", "note": "Routed to settlement-service"},
            {"state": "SETTLING",  "timestamp": "2024-01-15 10:30:01", "note": "Settlement initiated"},
            {"state": "FAILED",    "timestamp": "2024-01-15 10:33:47", "note": "Settlement timeout after 3m 46s"},
        ],
        "error": "Settlement service did not respond within SLA (180s). Trade marked FAILED.",
        "reprocessed": False,
        "business_impact": "AAPL BUY order for 5,000 shares not executed. Client position not updated.",
        "financial_exposure": 937100.00,
    },
    "22222": {
        "trade_id": "22222", "instrument": "TSLA", "direction": "SELL",
        "quantity": 1200, "price": 242.10, "trader": "sara.jones@firm.com",
        "status": "REJECTED", "sla_breach": False,
        "lifecycle": [
            {"state": "RECEIVED",  "timestamp": "2024-01-15 11:02:00", "note": "Trade received from OMS"},
            {"state": "VALIDATED", "timestamp": "2024-01-15 11:02:01", "note": "Passed format validation"},
            {"state": "REJECTED",  "timestamp": "2024-01-15 11:02:03", "note": "Duplicate detected — matches trade 22198"},
        ],
        "error": "Duplicate trade. Original ID: 22198 submitted at 10:58:44.",
        "reprocessed": False, "duplicate_of": "22198",
        "business_impact": "Trade correctly rejected. No financial exposure. Trader notified.",
        "financial_exposure": 0,
    },
    "33333": {
        "trade_id": "33333", "instrument": "MSFT", "direction": "BUY",
        "quantity": 3000, "price": 415.80, "trader": "mike.chen@firm.com",
        "status": "PENDING", "sla_breach": True,
        "lifecycle": [
            {"state": "RECEIVED",  "timestamp": "2024-01-15 14:15:00", "note": "Trade received from OMS"},
            {"state": "VALIDATED", "timestamp": "2024-01-15 14:15:01", "note": "Passed pre-trade risk checks"},
            {"state": "ROUTED",    "timestamp": "2024-01-15 14:15:03", "note": "Routed to settlement-service"},
            {"state": "PENDING",   "timestamp": "2024-01-15 14:20:00", "note": "Awaiting settlement — service degraded"},
        ],
        "error": "Settlement service full outage since 14:18. 47 trades queued.",
        "reprocessed": False,
        "business_impact": "MSFT BUY pending. 47 trades affected. T+2 settlement deadline at risk.",
        "financial_exposure": 1247400.00,
    },
    "44444": {
        "trade_id": "44444", "instrument": "GOOGL", "direction": "BUY",
        "quantity": 800, "price": 175.25, "trader": "priya.patel@firm.com",
        "status": "SETTLED", "sla_breach": True,
        "lifecycle": [
            {"state": "RECEIVED",  "timestamp": "2024-01-15 09:00:00", "note": "Trade received from OMS"},
            {"state": "VALIDATED", "timestamp": "2024-01-15 09:00:01", "note": "Passed pre-trade risk checks"},
            {"state": "ROUTED",    "timestamp": "2024-01-15 09:00:03", "note": "Routed to settlement-service"},
            {"state": "SETTLING",  "timestamp": "2024-01-15 09:00:10", "note": "Settlement initiated"},
            {"state": "SETTLED",   "timestamp": "2024-01-15 09:08:44", "note": "Settled in 8m 34s (SLA: 2 mins)"},
        ],
        "error": None, "reprocessed": False,
        "settlement_duration_seconds": 514, "sla_threshold_seconds": 120,
        "business_impact": "Trade settled but 4x slower than SLA. Compliance team notified.",
        "financial_exposure": 0,
    },
    "55555": {
        "trade_id": "55555", "instrument": "NVDA", "direction": "BUY",
        "quantity": 10000, "price": 875.00, "trader": "alex.wong@firm.com",
        "status": "REJECTED", "sla_breach": False,
        "lifecycle": [
            {"state": "RECEIVED",  "timestamp": "2024-01-15 13:30:00", "note": "Trade received from OMS"},
            {"state": "VALIDATED", "timestamp": "2024-01-15 13:30:01", "note": "Passed format validation"},
            {"state": "REJECTED",  "timestamp": "2024-01-15 13:30:02", "note": "Risk engine hard reject"},
        ],
        "error": "Trade exceeds notional limit. $8,750,000 breaches trader limit of $5,000,000.",
        "reprocessed": False, "notional_value": 8_750_000, "trader_limit": 5_000_000,
        "business_impact": "NVDA BUY blocked by risk controls. Risk desk approval required.",
        "financial_exposure": 0,
    },
}

DATADOG_APM = {
    "12345": {
        "trace_id": "apm-trace-12345",
        "root_service": "trade-router",
        "total_duration_ms": 226180,
        "status": "ERROR",
        "layer": "INFRASTRUCTURE",
        "app_root_cause": "DB connection pool exhaustion caused by OOMKill cycle in settlement-service.",
        "spans": [
            {"service": "trade-router",       "operation": "route_trade",           "duration_ms": 12,     "status": "OK"},
            {"service": "settlement-service", "operation": "initiate_settlement",   "duration_ms": 226100, "status": "ERROR",
             "error": "SocketTimeoutException: Read timed out after 180000ms"},
            {"service": "settlement-service", "operation": "acquire_db_connection", "duration_ms": 45000,  "status": "ERROR",
             "error": "HikariPool: Connection not available after 30000ms"},
        ],
    },
    "22222": {
        "trace_id": "apm-trace-22222",
        "root_service": "trade-router",
        "total_duration_ms": 3,
        "status": "OK",
        "layer": "APP_LOGIC",
        "app_root_cause": "No error. Duplicate detection worked as designed.",
        "spans": [
            {"service": "trade-router",  "operation": "route_trade",         "duration_ms": 1, "status": "OK"},
            {"service": "dedup-service", "operation": "lookup_recent_trades", "duration_ms": 2, "status": "OK",
             "note": "Duplicate correctly detected within SLA"},
        ],
    },
    "33333": {
        "trace_id": "apm-trace-33333",
        "root_service": "trade-router",
        "total_duration_ms": 300000,
        "status": "ERROR",
        "layer": "INFRASTRUCTURE",
        "app_root_cause": "Oracle connection pool exhausted (ORA-12516). All settlement pods crash-looping.",
        "spans": [
            {"service": "trade-router",       "operation": "route_trade",         "duration_ms": 5,      "status": "OK"},
            {"service": "settlement-service", "operation": "initiate_settlement", "duration_ms": 299990, "status": "ERROR",
             "error": "ServiceUnavailableException: 503"},
            {"service": "settlement-service", "operation": "get_db_connection",   "duration_ms": 100,    "status": "ERROR",
             "error": "OracleException: ORA-12516 listener refused connection"},
        ],
    },
    "44444": {
        "trace_id": "apm-trace-44444",
        "root_service": "trade-router",
        "total_duration_ms": 514000,
        "status": "OK",
        "layer": "DATABASE",
        "app_root_cause": "Missing index on SETTLEMENT_DATE causing full table scan. Schema issue not app logic.",
        "spans": [
            {"service": "trade-router",       "operation": "route_trade",           "duration_ms": 4,      "status": "OK"},
            {"service": "settlement-service", "operation": "fetch_settlement_data", "duration_ms": 498000, "status": "SLOW",
             "note": "Oracle full table scan — missing index on SETTLEMENT_DATE"},
            {"service": "fee-calculator",     "operation": "calculate_fees",        "duration_ms": 4,      "status": "OK"},
        ],
    },
    "55555": {
        "trace_id": "apm-trace-55555",
        "root_service": "trade-router",
        "total_duration_ms": 2,
        "status": "OK",
        "layer": "BUSINESS_RULE",
        "app_root_cause": "No error. Risk engine enforced notional limit correctly.",
        "spans": [
            {"service": "trade-router", "operation": "route_trade",          "duration_ms": 1, "status": "OK"},
            {"service": "risk-engine",  "operation": "check_notional_limit", "duration_ms": 1, "status": "OK",
             "note": "Hard reject. $8.75M > $5M limit."},
        ],
    },
}

APP_EVENTS = {
    "12345": [
        {"timestamp": "2024-01-15 09:47:02", "type": "VALIDATION_PASSED",  "service": "validation-service", "message": "All pre-trade validations passed",      "business_context": "Trade cleared for execution"},
        {"timestamp": "2024-01-15 10:30:01", "type": "SETTLEMENT_STARTED", "service": "settlement-service", "message": "Settlement process initiated",           "business_context": "Money movement process started"},
        {"timestamp": "2024-01-15 10:33:47", "type": "SETTLEMENT_TIMEOUT", "service": "settlement-service", "message": "Settlement SLA breached — 226s vs 180s", "business_context": "Trade failed to settle within regulatory window"},
        {"timestamp": "2024-01-15 10:33:48", "type": "TRADE_FAILED",       "service": "trade-router",       "message": "Trade 12345 moved to FAILED",            "business_context": "Client order not fulfilled. Manual reprocessing required."},
    ],
    "22222": [
        {"timestamp": "2024-01-15 11:02:00", "type": "TRADE_RECEIVED",      "service": "trade-router",         "message": "New TSLA sell order received",          "business_context": "Order from sara.jones@firm.com"},
        {"timestamp": "2024-01-15 11:02:03", "type": "DUPLICATE_CONFIRMED", "service": "dedup-service",        "message": "Duplicate of trade 22198 confirmed",   "business_context": "System prevented double execution. Working as designed."},
        {"timestamp": "2024-01-15 11:02:04", "type": "NOTIFICATION_SENT",   "service": "notification-service", "message": "Rejection email sent to trader",       "business_context": "Trader informed of rejection reason"},
    ],
    "33333": [
        {"timestamp": "2024-01-15 14:15:01", "type": "VALIDATION_PASSED", "service": "validation-service", "message": "All pre-trade validations passed",        "business_context": "Trade cleared for execution"},
        {"timestamp": "2024-01-15 14:18:00", "type": "SERVICE_OUTAGE",    "service": "settlement-service", "message": "Settlement service unavailable",          "business_context": "47 trades cannot proceed. T+2 deadline at risk."},
        {"timestamp": "2024-01-15 14:20:00", "type": "INCIDENT_RAISED",   "service": "incident-manager",   "message": "P1 incident raised: INC-2024-0847",      "business_context": "Engineering team alerted. Resolution in progress."},
    ],
    "44444": [
        {"timestamp": "2024-01-15 09:04:00", "type": "SLA_WARNING",       "service": "sla-monitor",        "message": "Settlement approaching SLA limit",        "business_context": "Settlement running slower than expected"},
        {"timestamp": "2024-01-15 09:08:44", "type": "TRADE_SETTLED",     "service": "settlement-service", "message": "Trade settled in 8m 34s",                 "business_context": "Complete but SLA breached. Compliance notified."},
        {"timestamp": "2024-01-15 09:09:00", "type": "SLA_BREACH_LOGGED", "service": "compliance-service", "message": "SLA breach recorded — 514s vs 120s",      "business_context": "May require regulatory reporting."},
    ],
    "55555": [
        {"timestamp": "2024-01-15 13:30:02", "type": "RISK_LIMIT_BREACH", "service": "risk-engine",         "message": "$8,750,000 exceeds $5,000,000 limit",    "business_context": "Trade value exceeds trader authorisation"},
        {"timestamp": "2024-01-15 13:30:02", "type": "TRADE_REJECTED",    "service": "risk-engine",         "message": "Hard rejected by risk engine",            "business_context": "Blocked. Risk desk approval required to proceed."},
        {"timestamp": "2024-01-15 13:30:03", "type": "ESCALATION_SENT",   "service": "notification-service","message": "Escalation sent to risk-desk@firm.com",   "business_context": "Risk team notified."},
    ],
}

DATADOG_ALERTS = {
    "12345": [
        {"id": "mon-001", "title": "Settlement P99 Latency Critical", "status": "ALERT", "severity": "CRITICAL", "service": "settlement-service", "triggered_at": "2024-01-15 10:30:00", "message": "P99 latency 47s. Threshold 10s."},
        {"id": "mon-002", "title": "EKS Pod Restart settlement",      "status": "ALERT", "severity": "HIGH",     "service": "settlement-service", "triggered_at": "2024-01-15 10:31:00", "message": "Pod restarted 2x in 5 mins. OOMKilled."},
        {"id": "mon-003", "title": "Kafka Lag settlement-topic",      "status": "ALERT", "severity": "HIGH",     "service": "kafka",              "triggered_at": "2024-01-15 10:29:00", "message": "Lag 45,230 msgs. Baseline <500."},
    ],
    "22222": [{"id": "mon-010", "title": "Duplicate Rate Elevated", "status": "WARN", "severity": "MEDIUM", "service": "trade-router", "triggered_at": "2024-01-15 11:00:00", "message": "12x above baseline."}],
    "33333": [
        {"id": "mon-020", "title": "Settlement Full Outage",      "status": "ALERT", "severity": "CRITICAL", "service": "settlement-service", "triggered_at": "2024-01-15 14:18:00", "message": "All pods CrashLoopBackOff. 47 trades queued."},
        {"id": "mon-021", "title": "Oracle Connection Pool Full", "status": "ALERT", "severity": "CRITICAL", "service": "oracle-db",          "triggered_at": "2024-01-15 14:17:00", "message": "100% capacity. ORA-12516."},
        {"id": "mon-022", "title": "Trade Queue Critical",        "status": "ALERT", "severity": "HIGH",     "service": "trade-router",       "triggered_at": "2024-01-15 14:20:00", "message": "47 pending."},
    ],
    "44444": [
        {"id": "mon-030", "title": "Settlement Degraded",  "status": "WARN", "severity": "MEDIUM", "service": "settlement-service", "triggered_at": "2024-01-15 08:55:00", "message": "Avg 6.2 mins. SLA: 2 mins."},
        {"id": "mon-031", "title": "Oracle Slow Queries",  "status": "WARN", "severity": "MEDIUM", "service": "oracle-db",          "triggered_at": "2024-01-15 08:50:00", "message": "Missing index on SETTLEMENT_DATE."},
    ],
    "55555": [{"id": "mon-040", "title": "Risk Notional Breach Volume High", "status": "WARN", "severity": "LOW", "service": "risk-engine", "triggered_at": "2024-01-15 13:00:00", "message": "3 breaches last hour."}],
}

DATADOG_LOGS = {
    "12345": [
        {"timestamp": "2024-01-15 10:29:58", "level": "WARN",     "service": "settlement-service", "message": "Kafka lag rising — 12,000 behind"},
        {"timestamp": "2024-01-15 10:31:14", "level": "ERROR",    "service": "settlement-service", "message": "OOMKilled — pod restarting"},
        {"timestamp": "2024-01-15 10:33:47", "level": "ERROR",    "service": "settlement-service", "message": "Trade 12345 timeout 226s. Marking FAILED."},
    ],
    "22222": [
        {"timestamp": "2024-01-15 11:02:02", "level": "WARN",  "service": "dedup-service", "message": "Potential duplicate — checking history"},
        {"timestamp": "2024-01-15 11:02:03", "level": "ERROR", "service": "dedup-service", "message": "Duplicate confirmed vs 22198. Rejecting."},
    ],
    "33333": [
        {"timestamp": "2024-01-15 14:17:02", "level": "ERROR",    "service": "oracle-db",          "message": "Connection pool exhausted"},
        {"timestamp": "2024-01-15 14:18:00", "level": "CRITICAL", "service": "settlement-service",  "message": "All retries failed. CrashLoopBackOff."},
    ],
    "44444": [
        {"timestamp": "2024-01-15 09:02:00", "level": "WARN", "service": "oracle-db",          "message": "Full table scan on SETTLEMENT_DATE — missing index"},
        {"timestamp": "2024-01-15 09:08:44", "level": "INFO", "service": "settlement-service", "message": "Trade 44444 settled — 8m 34s. SLA breached."},
    ],
    "55555": [
        {"timestamp": "2024-01-15 13:30:01", "level": "WARN",  "service": "risk-engine", "message": "Notional $8.75M approaching limit $5M"},
        {"timestamp": "2024-01-15 13:30:02", "level": "ERROR", "service": "risk-engine", "message": "Hard reject — exceeds limit by $3.75M"},
    ],
}

KAFKA_LAG = {
    "12345": {"snapshot_time": "2024-01-15 10:33:00", "topics": [{"topic": "settlement-topic", "total_lag": 45_230, "status": "CRITICAL"}, {"topic": "trade-events", "total_lag": 120, "status": "HEALTHY"}], "pattern": "Same spike 2024-01-09 — also Tuesday."},
    "22222": {"snapshot_time": "2024-01-15 11:02:00", "topics": [{"topic": "trade-events", "total_lag": 85, "status": "HEALTHY"}], "pattern": "No issues."},
    "33333": {"snapshot_time": "2024-01-15 14:20:00", "topics": [{"topic": "settlement-topic", "total_lag": 127_450, "status": "CRITICAL"}, {"topic": "trade-events", "total_lag": 890, "status": "WARN"}], "pattern": "Full consumer stop."},
    "44444": {"snapshot_time": "2024-01-15 09:08:00", "topics": [{"topic": "settlement-topic", "total_lag": 3_200, "status": "WARN"}], "pattern": "Correlates with slow DB queries."},
    "55555": {"snapshot_time": "2024-01-15 13:30:00", "topics": [{"topic": "trade-events", "total_lag": 95, "status": "HEALTHY"}], "pattern": "No issues."},
}

EKS_PODS = {
    "12345": {"snapshot_time": "2024-01-15 10:34:00", "namespace": "trading-prod", "pods": [{"name": "settlement-service-7d9f8b-xk2pq", "status": "CrashLoopBackOff", "restarts": 2, "reason": "OOMKilled — 512Mi exceeded"}, {"name": "settlement-service-7d9f8b-mn7rs", "status": "Running", "restarts": 0}], "hpa": {"current_replicas": 2, "desired_replicas": 4, "note": "Scaling delayed"}},
    "22222": {"snapshot_time": "2024-01-15 11:02:00", "namespace": "trading-prod", "pods": [{"name": "trade-router-6c4d9f-pp2lx", "status": "Running", "restarts": 0}], "hpa": None},
    "33333": {"snapshot_time": "2024-01-15 14:20:00", "namespace": "trading-prod", "pods": [{"name": "settlement-service-7d9f8b-xk2pq", "status": "CrashLoopBackOff", "restarts": 7, "reason": "ORA-12516"}, {"name": "settlement-service-7d9f8b-mn7rs", "status": "CrashLoopBackOff", "restarts": 6, "reason": "ORA-12516"}, {"name": "settlement-service-7d9f8b-rt9vw", "status": "CrashLoopBackOff", "restarts": 5, "reason": "ORA-12516"}], "hpa": {"current_replicas": 3, "desired_replicas": 3, "note": "All crashing. Root cause is DB."}},
    "44444": {"snapshot_time": "2024-01-15 09:08:00", "namespace": "trading-prod", "pods": [{"name": "settlement-service-7d9f8b-xk2pq", "status": "Running", "restarts": 0, "cpu": "410m/500m"}], "hpa": {"current_replicas": 1, "desired_replicas": 2, "note": "HPA triggered"}},
    "55555": {"snapshot_time": "2024-01-15 13:30:00", "namespace": "trading-prod", "pods": [{"name": "risk-engine-5f7c2d-ab3xy", "status": "Running", "restarts": 0}], "hpa": None},
}

MANAGER_SUMMARY = {
    "12345": {"trades_affected": 1, "sla_breach": True, "financial_exposure": "$937,100", "pattern": "Recurring — same failure last Tuesday 2024-01-09", "incident": None, "resolution_owner": "Platform Engineering", "action_required": "Approve memory limit increase for settlement pods."},
    "22222": {"trades_affected": 1, "sla_breach": False, "financial_exposure": "$0", "pattern": "Isolated", "incident": None, "resolution_owner": "None — system worked correctly", "action_required": "Investigate why OMS resubmitted."},
    "33333": {"trades_affected": 47, "sla_breach": True, "financial_exposure": "$47M+ (all queued)", "pattern": "New incident INC-2024-0847", "incident": "INC-2024-0847 P1", "resolution_owner": "Platform Engineering + DBA", "action_required": "Urgent: DBA increase Oracle pool. Restart pods after fix."},
    "44444": {"trades_affected": 1, "sla_breach": True, "financial_exposure": "$0 (settled)", "pattern": "3rd SLA breach this week", "incident": None, "resolution_owner": "DBA team", "action_required": "Add index on SETTLEMENT_DATE in Oracle."},
    "55555": {"trades_affected": 1, "sla_breach": False, "financial_exposure": "$0", "pattern": "3rd notional breach this hour", "incident": None, "resolution_owner": "Risk Desk", "action_required": "Review alex.wong limits or approve escalation."},
}


def get_trade_context(trade_id: str) -> dict:
    """Returns all data for a given trade across all sources."""
    tid = str(trade_id)
    return {
        "oracle":          ORACLE_TRADES.get(tid,  {"error": f"Trade {tid} not found"}),
        "datadog_alerts":  DATADOG_ALERTS.get(tid, []),
        "datadog_logs":    DATADOG_LOGS.get(tid,   []),
        "datadog_apm":     DATADOG_APM.get(tid,    {}),
        "app_events":      APP_EVENTS.get(tid,     []),
        "kafka":           KAFKA_LAG.get(tid,       {}),
        "eks":             EKS_PODS.get(tid,        {}),
        "manager_summary": MANAGER_SUMMARY.get(tid, {}),
    }
