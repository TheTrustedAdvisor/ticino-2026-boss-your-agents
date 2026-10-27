# Plan: Sales semantic model for account managers (task/sales-request.md, Giulia, Sales Operations)

Workspace: FF Ticino Session 2 DEV (<workspace-2-id>), empty at start.
Identity: builder@contoso.example (builder). Prior wiki read: ADR-001, ADR-002, ADR-003, ADR-004, the five
decision pages, DRF-000, SEC-010.

## Items

| Item | Type | Name | Basis |
|---|---|---|---|
| Lakehouse | Lakehouse | `lh_sales` | ADR-004 (prefix `lh_`), ADR-001 (no schemas) |
| Delta tables | in `lh_sales` | `customers`, `orders` | ADR-001 (upload to `Files/raw/`, `load-table --engine onelake`) |
| Semantic model | SemanticModel | `sm_sales` | ADR-004 (prefix `sm_`), ADR-002 (Direct Lake on OneLake) |

## Steps

1. `lakehouse create lh_sales` (no `--schemas`, ADR-001).
2. Upload `data/customers.csv`, `data/orders.csv` to `Files/raw/`; `load-table` each with the OneLake engine
   (ADR-001: Spark Load Table API throttled on F2). Check `lakehouse schema` for column types.
3. Write `work/sm_sales/` (definition.pbism + TMDL):
   - `expressions.tmdl`: shared expression `AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<ws id>/<lakehouse id>")` (ADR-002).
   - `tables/Customers.tmdl` (entity `customers`, no `schemaName`): Customer Name, Region, Account Manager
     (from `account_manager_upn`), Credit Limit; `customer_id` hidden key. Measure `Number of Customers` = `COUNTROWS(Customers)`.
   - `tables/Orders.tmdl` (entity `orders`): hidden keys/amount columns, Order Date; measure `Revenue` = `SUM(Orders[Amount])`.
   - `relationships.tmdl`: Orders[Customer Id] -> Customers[Customer Id], many-to-one, single direction.
   - `roles/Account Manager.tmdl`: modelPermission read, `Customers[Account Manager] = USERPRINCIPALNAME()` (ADR-003).
4. `model lint`, then `model deploy work/sm_sales --name sm_sales`; `model query` to check the measures.
5. `model members add` for in-tenant account managers only (ADR-003): `viewer@contoso.example`.
   `giulia.bernasconi@example.com` and `luca.ferrari@example.com` are not tenant users; not added, open point for Sales Ops.

## How the model is secured, and why

- "Every account manager should be able to use it" = each manager opens the model and sees only their own
  customers (Credit Limit and revenue are sensitive). One dynamic role, filter on the mapping column, reaches
  Orders over the single-direction relationship (ADR-003; https://learn.microsoft.com/fabric/security/service-admin-row-level-security).
- Direct Lake on OneLake: no DirectQuery fallback, supports semantic-model RLS (ADR-002;
  https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#comparison-of-storage-modes).
- RLS only applies to users without Write: account managers must be workspace Viewer or item Read only, never
  Contributor+ (https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#data-access-rule-options).
  The reviewer cannot read workspace roles (SEC-010): a workspace admin must confirm this.
- Open point carried over (ADR-003): Docs strongly recommend a fixed-identity cloud connection with SSO disabled
  for semantic-model RLS; under SSO users need Read+ReadAll on `lh_sales` and could bypass RLS through OneLake.
  The toolkit cannot create connections; a workspace admin binds one. Users get no item permission on `lh_sales`.

## Governance

- Every decision recorded as its own wiki page (category `decision`) when made.
- New workspace, so there is no signed baseline for it (cf. DRF-000); the builder never signs snapshots or runs the gate.
