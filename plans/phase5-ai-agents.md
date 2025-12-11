# Phase 5: AI Agents

## Overview

**Status:** 📋 Planned  
**Dependencies:** Phase 4 (Use Cases)  
**Estimated Effort:** 4-6 weeks  
**Reference:** [Databricks AI Agents](https://docs.databricks.com/generative-ai/agent-framework.html)

---

## Purpose

Phase 5 creates specialized AI agents that:
1. **Provide domain expertise** - Deep knowledge per business domain
2. **Enable conversational analytics** - Natural language interactions
3. **Automate insights** - Proactive recommendations and alerts
4. **Orchestrate actions** - Execute workflows based on analysis

---

## Agent Architecture

### Multi-Agent Framework

```
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │     Agent       │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │ Revenue │        │Engagement│        │ Property│
    │  Agent  │        │  Agent   │        │  Agent  │
    └────┬────┘        └────┬────┘        └────┬────┘
         │                   │                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │  Host   │        │Customer │        │  Data   │
    │  Agent  │        │  Agent  │        │  Agent  │
    └─────────┘        └─────────┘        └─────────┘
```

---

## Agent Summary

| # | Agent | Domain | Primary Function | Key Capabilities |
|---|-------|--------|-----------------|------------------|
| 1 | Revenue Agent | 💰 Revenue | Financial analysis & forecasting | Revenue trends, forecasting, anomalies |
| 2 | Engagement Agent | 📊 Engagement | Marketing optimization | Conversion analysis, funnel insights |
| 3 | Property Agent | 🏠 Property | Inventory management | Pricing, availability, optimization |
| 4 | Host Agent | 👤 Host | Partner success | Performance tracking, recommendations |
| 5 | Customer Agent | 🎯 Customer | Customer success | Segmentation, LTV, retention |
| 6 | Orchestrator | 🎭 All | Multi-agent coordination | Route queries, aggregate insights |

---

## 💰 Revenue Agent

### Capabilities

| Capability | Description | Tools Used |
|------------|-------------|------------|
| Revenue Analysis | Analyze revenue trends and patterns | TVFs, Metric Views |
| Forecasting | Predict future revenue | ML Models |
| Anomaly Detection | Identify unusual revenue patterns | Monitors |
| Comparison | Compare periods, destinations, properties | TVFs |
| Recommendations | Suggest revenue optimization actions | ML Models |

### System Prompt

```
You are the Revenue Agent for Wanderbricks, a vacation rental analytics platform.

## Your Expertise
- Revenue trends and forecasting
- Booking value analysis
- Payment and cancellation tracking
- Financial KPI monitoring
- Revenue optimization recommendations

## Available Tools
- get_revenue_by_period(start_date, end_date, time_grain)
- get_top_properties_by_revenue(start_date, end_date, top_n)
- get_revenue_by_destination(start_date, end_date)
- get_cancellation_analysis(start_date, end_date)
- get_payment_metrics(start_date, end_date)
- predict_revenue(start_date, end_date)  # ML model

## Guidelines
1. Always provide data-driven insights with specific numbers
2. Compare metrics to previous periods for context
3. Identify trends and patterns proactively
4. Suggest actionable recommendations when appropriate
5. Format currency as $X,XXX.XX
6. Default to last 30 days if no date range specified

## Response Format
- Start with a concise summary
- Provide key metrics
- Explain trends or anomalies
- Offer recommendations if relevant
```

### Example Interactions

**User:** How was revenue last month?

**Agent:** Last month's revenue was **$1.2M**, up 15% from the previous month.

**Key Highlights:**
- **Total Bookings:** 2,450 (+12% MoM)
- **Average Booking Value:** $490 (+3% MoM)
- **Cancellation Rate:** 8.5% (stable)

**Top Performers:**
1. Paris properties: $180K (15% of total)
2. Rome properties: $145K (12% of total)
3. Barcelona properties: $120K (10% of total)

**Recommendation:** Revenue growth is strong. Consider increasing marketing spend in Paris to capitalize on demand.

---

## 📊 Engagement Agent

### Capabilities

| Capability | Description | Tools Used |
|------------|-------------|------------|
| Funnel Analysis | View → Click → Book conversion | TVFs |
| Traffic Analysis | Source and device breakdown | TVFs |
| Content Optimization | Identify underperforming listings | TVFs, Monitors |
| Campaign Tracking | Marketing effectiveness | Custom queries |
| Conversion Prediction | Predict booking probability | ML Models |

### System Prompt

```
You are the Engagement Agent for Wanderbricks, a vacation rental analytics platform.

## Your Expertise
- Conversion funnel optimization
- Traffic source analysis
- Property engagement metrics
- Marketing campaign effectiveness
- Content and UX insights

## Available Tools
- get_property_engagement(start_date, end_date, property_id_filter)
- get_conversion_funnel(start_date, end_date)
- get_traffic_source_analysis(start_date, end_date)
- get_device_engagement(start_date, end_date)
- predict_conversion(property_id, user_context)  # ML model

## Guidelines
1. Express conversion rates as percentages (e.g., 3.2%)
2. Compare against benchmarks when available
3. Identify optimization opportunities
4. Suggest A/B testing ideas
5. Prioritize high-impact recommendations
```

---

## 🏠 Property Agent

### Capabilities

| Capability | Description | Tools Used |
|------------|-------------|------------|
| Portfolio Analysis | Inventory overview and trends | TVFs |
| Pricing Optimization | Recommend optimal prices | ML Models |
| Performance Tracking | Property-level KPIs | TVFs, Metric Views |
| Availability Management | Inventory by destination | TVFs |
| Amenity Analysis | Feature correlation with bookings | TVFs |

### System Prompt

```
You are the Property Agent for Wanderbricks, a vacation rental analytics platform.

## Your Expertise
- Property portfolio management
- Pricing strategy optimization
- Inventory and capacity planning
- Property performance analysis
- Listing optimization

## Available Tools
- get_property_performance(start_date, end_date, destination_filter)
- get_availability_by_destination(start_date, end_date)
- get_pricing_analysis(start_date, end_date)
- get_property_type_analysis(start_date, end_date)
- optimize_price(property_id, target_date)  # ML model

## Guidelines
1. Consider seasonality in pricing recommendations
2. Compare properties against market averages
3. Identify underperforming listings
4. Suggest listing improvements
5. Account for local market conditions
```

---

## 👤 Host Agent

### Capabilities

| Capability | Description | Tools Used |
|------------|-------------|------------|
| Performance Tracking | Host-level KPIs | TVFs |
| Quality Analysis | Rating and verification impact | TVFs |
| Retention Analysis | Churn prediction and prevention | ML Models |
| Benchmarking | Compare against peer hosts | TVFs |
| Success Recommendations | Actionable improvement suggestions | AI |

### System Prompt

```
You are the Host Agent for Wanderbricks, a vacation rental analytics platform.

## Your Expertise
- Host performance tracking
- Quality and rating analysis
- Host retention and success
- Partner relationship management
- Host onboarding support

## Available Tools
- get_host_performance(start_date, end_date, host_id_filter)
- get_host_quality_metrics(start_date, end_date)
- get_host_retention_analysis(start_date, end_date)
- get_host_geographic_distribution()

## Guidelines
1. Be supportive and constructive in feedback
2. Highlight positive achievements
3. Offer specific, actionable recommendations
4. Compare against platform benchmarks
5. Identify hosts at risk of churning
```

---

## 🎯 Customer Agent

### Capabilities

| Capability | Description | Tools Used |
|------------|-------------|------------|
| Segmentation | Customer segment analysis | TVFs, ML |
| LTV Prediction | Lifetime value calculation | ML Models |
| Behavior Analysis | Booking patterns and preferences | TVFs |
| Retention | Churn risk and prevention | ML Models |
| Personalization | Recommendation generation | AI |

### System Prompt

```
You are the Customer Agent for Wanderbricks, a vacation rental analytics platform.

## Your Expertise
- Customer segmentation
- Lifetime value analysis
- Booking behavior patterns
- Customer retention strategies
- Personalization and recommendations

## Available Tools
- get_customer_segments(start_date, end_date)
- get_customer_ltv(start_date, end_date)
- get_booking_frequency_analysis(start_date, end_date)
- get_business_vs_leisure_analysis(start_date, end_date)
- predict_customer_ltv(user_id)  # ML model

## Guidelines
1. Segment customers meaningfully
2. Identify high-value customers
3. Suggest retention strategies
4. Personalize recommendations
5. Consider privacy in customer analysis
```

---

## 🎭 Orchestrator Agent

### Purpose
Route user queries to appropriate specialist agents and aggregate insights.

### System Prompt

```
You are the Orchestrator Agent for Wanderbricks analytics platform.

## Your Role
- Route queries to specialist agents
- Aggregate insights from multiple agents
- Provide executive summaries
- Handle cross-domain questions

## Specialist Agents Available
1. Revenue Agent: Financial metrics, forecasting, booking analysis
2. Engagement Agent: Marketing, conversion, traffic analysis
3. Property Agent: Inventory, pricing, listing management
4. Host Agent: Partner performance, quality, retention
5. Customer Agent: Segmentation, LTV, behavior analysis

## Routing Guidelines
- Revenue questions → Revenue Agent
- Marketing/conversion questions → Engagement Agent
- Property/pricing questions → Property Agent
- Host questions → Host Agent
- Customer questions → Customer Agent
- Cross-domain questions → Multiple agents, then synthesize

## Response Format for Cross-Domain
1. Identify relevant domains
2. Query each specialist agent
3. Synthesize insights
4. Provide unified recommendation
```

---

## Agent Tools Integration

### Tool Definitions

```python
from langchain.tools import tool

@tool
def get_revenue_by_period(start_date: str, end_date: str, time_grain: str = "day") -> str:
    """
    Get revenue metrics aggregated by time period.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        time_grain: Aggregation grain (day, week, month)
    
    Returns:
        Revenue metrics as formatted string
    """
    result = spark.sql(f"""
        SELECT * FROM {catalog}.{gold_schema}.get_revenue_by_period(
            '{start_date}', '{end_date}', '{time_grain}'
        )
    """)
    return format_revenue_response(result)
```

### Tool Registry

| Agent | Tools Count | Tool Categories |
|-------|-------------|-----------------|
| Revenue Agent | 7 | TVFs (6) + ML (1) |
| Engagement Agent | 6 | TVFs (5) + ML (1) |
| Property Agent | 6 | TVFs (5) + ML (1) |
| Host Agent | 4 | TVFs (4) |
| Customer Agent | 6 | TVFs (5) + ML (1) |
| Orchestrator | 6 | Agent calls (5) + Synthesis (1) |

---

## Implementation Architecture

### Model Serving

```python
from databricks.agents import AgentFramework

# Initialize agent framework
agent_framework = AgentFramework()

# Register Revenue Agent
revenue_agent = agent_framework.create_agent(
    name="revenue_agent",
    model="databricks-dbrx-instruct",
    system_prompt=REVENUE_SYSTEM_PROMPT,
    tools=[
        get_revenue_by_period,
        get_top_properties_by_revenue,
        get_revenue_by_destination,
        get_cancellation_analysis,
        get_payment_metrics,
        predict_revenue
    ],
    temperature=0.1,
    max_tokens=2000
)

# Deploy as endpoint
agent_framework.deploy_agent(
    agent=revenue_agent,
    endpoint_name="wanderbricks-revenue-agent",
    scale_to_zero=True
)
```

### Orchestrator Implementation

```python
class WanderbricksOrchestrator:
    """Multi-agent orchestrator for Wanderbricks."""
    
    def __init__(self):
        self.agents = {
            "revenue": RevenueAgent(),
            "engagement": EngagementAgent(),
            "property": PropertyAgent(),
            "host": HostAgent(),
            "customer": CustomerAgent()
        }
    
    def route_query(self, query: str) -> str:
        """Route query to appropriate agent(s)."""
        # Classify query domain
        domains = self.classify_domains(query)
        
        if len(domains) == 1:
            # Single domain - direct routing
            return self.agents[domains[0]].answer(query)
        else:
            # Multi-domain - aggregate responses
            responses = []
            for domain in domains:
                responses.append(self.agents[domain].answer(query))
            return self.synthesize_responses(responses)
    
    def classify_domains(self, query: str) -> list:
        """Classify query into relevant domains."""
        # Use LLM to classify
        classification = self.classifier.classify(query)
        return classification.domains
```

---

## Implementation Checklist

### Phase 5.1: Core Agents
- [ ] Implement Revenue Agent
- [ ] Implement Engagement Agent
- [ ] Implement Property Agent
- [ ] Implement Host Agent
- [ ] Implement Customer Agent

### Phase 5.2: Orchestration
- [ ] Implement Orchestrator Agent
- [ ] Build query routing logic
- [ ] Implement response synthesis
- [ ] Add cross-agent communication

### Phase 5.3: Deployment
- [ ] Deploy agent endpoints
- [ ] Configure auto-scaling
- [ ] Set up monitoring
- [ ] Implement feedback loop

### Phase 5.4: Integration
- [ ] Integrate with Genie Spaces
- [ ] Connect to dashboards
- [ ] Enable Slack integration
- [ ] Build API endpoints

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Query response time | <5 seconds |
| Query success rate | >95% |
| User satisfaction | >4.0/5.0 |
| Routing accuracy | >90% |
| Insight relevance | >85% |

---

## References

- [Databricks Agent Framework](https://docs.databricks.com/generative-ai/agent-framework.html)
- [LangChain Integration](https://docs.databricks.com/generative-ai/langchain.html)
- [Model Serving](https://docs.databricks.com/machine-learning/model-serving/)

