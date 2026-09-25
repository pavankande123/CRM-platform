# ENERMAX CRM — CUSTOM FIELD ARCHITECTURE & TRADEOFF ANALYSIS

## 1. Architectural Challenge

In multi-tenant SaaS systems, different client organizations need custom data attributes (e.g., Solar Installation Capacity in kW, GST Registration Category, Subsidy Token Number, Inverter Make) attached to core CRM entities (`customer`, `project`, `product`).

Modifying the physical relational database schema (`ALTER TABLE customers ADD COLUMN ...`) for each tenant has severe disadvantages:
- Requires transactional DDL or table locks.
- SQLite and older PostgreSQL versions struggle with dynamic concurrent DDL.
- Migration scripts become impossible to maintain when schema diverges per tenant.
- Rollbacks and operational disaster recovery become fragile.

---

## 2. Evaluated Architectural Options

| Approach | Description | Pros | Cons | Decision |
|---|---|---|---|---|
| **1. Dynamic DDL (Schema per Tenant)** | Execute `ALTER TABLE` whenever a custom field is created. | Native SQL queries, native column indexing. | DDL locks, schema drift, security risk, impossible SQLite compatibility. | **Rejected** |
| **2. Unstructured JSON Blob (`metadata` column)** | Store arbitrary JSON in an entity column. | Zero schema changes, fast schema-less writes. | Weak type safety, difficult relational constraints, difficult cross-entity reporting, index overhead in SQLite. | **Rejected for core fields** |
| **3. Pure EAV (Entity-Attribute-Value)** | Triple table: `(entity_id, attribute_id, value_string)`. | Highly flexible, easy to add fields. | Everything is a string, loss of native numeric/date math, terrible N+1 join performance. | **Rejected** |
| **4. Metadata-Driven Typed-Column Store (Chosen)** | Two tables: `custom_fields` (metadata definition) and `custom_field_values` with typed value columns (`value_text`, `value_numeric`, `value_date`, `value_boolean`). | Strong typing, native indexing, tenant isolation, supports validation & options, cross-database compatibility (PostgreSQL & SQLite). | Requires joining `custom_field_values` for custom field retrieval. | **ADOPTED** |

---

## 3. Chosen Design: Metadata-Driven Typed Custom Fields

### 3.1 Metadata Table: `custom_fields`
```sql
CREATE TABLE custom_fields (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL, -- 'customer', 'project', 'product'
    field_name VARCHAR(100) NOT NULL, -- e.g. 'solar_capacity_kw'
    display_name VARCHAR(150) NOT NULL, -- e.g. 'Solar Capacity (kW)'
    field_type VARCHAR(50) NOT NULL, -- 'text', 'number', 'currency', 'date', 'boolean', 'select'
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    is_searchable BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    options JSON, -- Array of string options for 'select' type: ["Residential", "Commercial", "Industrial"]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_custom_fields_tenant_entity_name UNIQUE (tenant_id, entity_type, field_name)
);
```

### 3.2 Value Table: `custom_field_values`
```sql
CREATE TABLE custom_field_values (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES custom_fields(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    value_text TEXT,
    value_numeric NUMERIC(18, 4),
    value_date DATE,
    value_boolean BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_custom_field_values UNIQUE (tenant_id, field_id, entity_id)
);
CREATE INDEX ix_custom_field_values_lookup ON custom_field_values (tenant_id, entity_type, entity_id);
```

---

## 4. Type Validation & Storage Rules

1. **Text**: Validated as string, stored in `value_text`.
2. **Number / Currency**: Validated as decimal/float, stored in `value_numeric`. Enables range filtering (`>`, `<`, `>=`).
3. **Date**: Validated as ISO date (`YYYY-MM-DD`), stored in `value_date`. Enables calendar range filtering.
4. **Boolean**: Validated as true/false, stored in `value_boolean`.
5. **Select**: Validated against `custom_fields.options` JSON array, stored in `value_text`.

---

## 5. Security & Isolation

- All queries filter on `tenant_id`.
- Creating or editing field definitions requires `crm:write` or `admin:manage`.
- Field names must be lowercase alphanumeric with underscores (`^[a-z0-9_]{2,50}$`) to prevent injection or invalid property names.
