# Part III: Query Federation

## Why federation is useful for exploration
Query federation allows a user to query data across multiple disparate systems (e.g., a SQL warehouse and an external Product API) as if they were in a single database, without having to first ingest and move all that data into a central storage layer.
It is extremely useful for exploration because:
1. **Speed to Insight**: Data engineers don't need to build complex ETL pipelines just to "peek" at data or join a small amount of external data with internal facts.
2. **Access to Live Data**: It allows joining historical warehouse data with "live" or "hot" data from external APIs or operational databases that hasn't been synced yet.
3. **Reduced Storage Costs**: You don't pay to store data that you only need to query occasionally.

## Risk and Control

**One Risk: Production Overload**
Federated queries often translate into direct calls against the source systems' resources (CPU, Memory, IO). A complex join involving a large warehouse table and a production transactional database (or API) could significantly slow down or даже crash the production system by consuming its resources or locking tables.

**One Control: Read Replicas / Caching**
To mitigate this risk, query federation should ideally target a **Read Replica** of the production database instead of the primary instance. Additionally, implement **Caching** layers or query limits (timeouts and row limits) to ensure that expensive cross-source queries don't run indefinitely and degrade source performance.
