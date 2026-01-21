"""
Wanderbricks Alerting Module

Config-driven alerting framework for Databricks SQL Alerts.

Components:
- setup_alert_rules.py: Creates alert_rules config table with 21 rules
- deploy_alerts.py: Deploys SQL alerts from config table

Alert Domains:
- Revenue (REV): Revenue, bookings, cancellations, payments
- Engagement (ENG): Traffic, conversion, property views
- Property (PROP): Inventory, pricing, zero-booking properties
- Host (HOST): Ratings, verification, activity
- Customer (CUST): Signups, churn, business customers

Alert Severity Levels:
- CRITICAL: Immediate action required, escalate to leadership
- WARNING: Investigate soon, domain owners notified
- INFO: Informational summaries, no action required

Usage:
    # Setup alert rules table
    databricks bundle run alert_rules_setup_job -t dev
    
    # Deploy alerts from config
    databricks bundle run alert_deploy_job -t dev
    
    # Dry run (validate without creating)
    databricks bundle run alert_deploy_job -t dev --dry_run=true
"""




