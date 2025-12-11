# Gold Layer Implementation - Quick Start

## 🚀 Deploy in 5 Commands (50 min)

```bash
# 1. Validate bundle (30 sec)
databricks bundle validate

# 2. Deploy all resources (3 min)
databricks bundle deploy -t dev

# 3. Create Gold tables from YAMLs (10-15 min)
databricks bundle run gold_setup_job -t dev

# 4. Populate from Silver (15-20 min)
databricks bundle run gold_merge_job -t dev

# 5. Setup Lakehouse Monitoring (5 min + 20 min initialization)
databricks bundle run lakehouse_monitoring_job -t dev
```

## ✅ Verify Success

```sql
-- Check tables created
USE CATALOG prashanth_subrahmanyam_catalog;
SHOW TABLES IN wanderbricks_gold;

-- Expected: 8 tables
-- ✓ dim_user
-- ✓ dim_host
-- ✓ dim_property
-- ✓ dim_destination
-- ✓ dim_date
-- ✓ fact_booking_detail
-- ✓ fact_booking_daily
-- ✓ fact_property_engagement

-- Check record counts
SELECT 'dim_user' as table_name, COUNT(*) as records FROM dim_user
UNION ALL
SELECT 'dim_host', COUNT(*) FROM dim_host
UNION ALL
SELECT 'dim_property', COUNT(*) FROM dim_property
UNION ALL
SELECT 'dim_destination', COUNT(*) FROM dim_destination
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'fact_booking_detail', COUNT(*) FROM fact_booking_detail
UNION ALL
SELECT 'fact_booking_daily', COUNT(*) FROM fact_booking_daily
UNION ALL
SELECT 'fact_property_engagement', COUNT(*) FROM fact_property_engagement;
```

## 📖 Full Guide

See [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for:
- Detailed architecture
- Troubleshooting
- Validation queries
- Performance considerations
- Next steps

## 🎯 What's Next?

After Gold layer:
1. **Metric Views** - Semantic layer for Genie
2. **Table-Valued Functions** - Parameterized queries
3. ✅ **Lakehouse Monitoring** - Quality and drift monitoring (IMPLEMENTED)
4. **AI/BI Dashboards** - Business dashboards
5. **Genie Space** - Natural language queries

### Monitoring Details

After running step 5 (lakehouse_monitoring_job):
- ⚠️ **Wait 15-20 minutes** for monitors to initialize
- Check status: Databricks UI → Data → Lakehouse Monitoring
- 5 monitors created: Revenue, Engagement, Property, Host, Customer
- 19 custom business metrics configured
- Full guide: [../src/wanderbricks_gold/MONITORING_README.md](../src/wanderbricks_gold/MONITORING_README.md)

