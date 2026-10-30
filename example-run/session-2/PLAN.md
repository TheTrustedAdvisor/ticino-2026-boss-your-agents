# Plan: Sales request (Giulia, Sales Operations) - session 2

Workspace: FF Ticino Session 2 DEV (a12f95a1-...), empty at start. Identity: builder@contoso.example (builder).
Request: `task/sales-request.md`. Data: `data/customers.csv` (60 rows, 3 account managers x 20 customers),
`data/orders.csv` (600 rows; all 60 customer ids exist in customers).

Wiki read before planning: ADR-001..ADR-006, the 8 decision pages, SEC-010, SEC-020, DRF-000, and
`wiki/rules/` (ADR-001, -002, -004, -005, -006 yaml).

## Items

| Item | Type | Name | Follows |
|---|---|---|---|
| Lakehouse | Lakehouse | `lh_sales` (no schemas) | ADR-005 (type prefixes, applies from this delivery), ADR-001 |
| Tables | Delta | `customers`, `orders` under `Tables/`, CSVs in `Files/raw/`, OneLake engine (no Spark) | ADR-001 |
| Semantic model | SemanticModel | `sm_sales` | ADR-005, ADR-002, ADR-003, ADR-004 |
| SQL endpoint policy | T-SQL objects in `lh_sales` endpoint | schema `rls`, TVF `rls.fn_account_manager`, policy `rls.customers_account_manager` | ADR-006, SEC-020 |

Model `sm_sales` (definition in `work/sm_sales/`):
- Direct Lake on OneLake: shared expression `AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<ws>/<lh>")`,
  partitions `mode: directLake`, no `schemaName` (lakehouse without schemas) (ADR-002).
- Star schema (ADR-003): `Customers` (Customer Name, Region, Account Manager, Credit Limit; key hidden),
  `Orders` (order_id, Order Date, amount; keys hidden), Orders[customer_id] *:1 Customers[customer_id], single direction.
  Measures `Revenue = SUM(Orders[amount])`, `Customer Count = COUNTROWS(Customers)`; numeric columns `summarizeBy: none`.

## How the model is secured

1. Semantic-model role `Account Managers` (modelPermission read), dynamic filter
   `Customers[account_manager_upn] = USERPRINCIPALNAME()`; reaches Orders through the relationship (ADR-004).
2. Role members: account managers whose UPN is a tenant user: `viewer@contoso.example`.
   `luca.ferrari@example.com` and `giulia.bernasconi@example.com` are not tenant users (ADR-004); they stay pending.
3. Same rule in the SQL analytics endpoint of `lh_sales` (ADR-006, answer to SEC-020): filter predicate on
   `dbo.customers(account_manager_upn)` matching `LOWER(USER_NAME())`, no exemption. Script `work/sql/customers-rls.sql`.
   The Direct Lake on OneLake model reads Delta files, not the endpoint, so it is unaffected.

Why: "every account manager should be able to use it" = one model, each AM sees only their own customers and
revenue; the rule must hold in every engine that can read the table (ADR-006).

## Known open items (not decided by this build; for the human)

- `dbo.orders` in the SQL endpoint has no policy (open item of ADR-006 / SEC-020).
- Spark/OneLake reads of `lh_sales` are not covered by the SQL policy.
- SEC-010: workspace role holders (Admin/Member/Contributor) bypass model RLS; a workspace admin must check.
- ADR-004: fixed-identity cloud connection or OneLake read for AMs, Viewer role/sharing: workspace admin.
- DRF-000: the signed baseline belongs to Session 1; this workspace has new items and needs its own approval.

## Sources

- https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview#automatic-table-discovery-and-registration
- https://learn.microsoft.com/fabric/fundamentals/direct-lake-develop#power-query-connectors
- https://learn.microsoft.com/fabric/fundamentals/direct-lake-power-bi-desktop#migrate-direct-lake-on-sql-semantic-models-to-direct-lake-on-onelake
- https://learn.microsoft.com/power-bi/guidance/star-schema
- https://learn.microsoft.com/fabric/security/service-admin-row-level-security
- https://learn.microsoft.com/fabric/data-warehouse/row-level-security
- https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-tenant-level-planning#workspace-naming-conventions
