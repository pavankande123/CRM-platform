# Enermax CRM — Phase 2 Operator UX & Workflow Specification

## 1. Operator Experience Philosophy

Enermax's CRM is built around a **single operator workflow**.
Traditional CRMs fail by scattering a single business relationship across 10 different disconnected tabs (leads, accounts, contacts, opportunities, cases, invoices).

The Enermax UX principle is:
> **EVERYTHING VISIBLE IN CONTEXT. NO UNNECESSARY CLICKS.**

---

## 2. Core Navigation Structure

```text
[ ENERMAX CRM ]
  │
  ├── Dashboard      (High-level operational overview & today's priorities)
  ├── Customers      (Searchable customer directory & unified Customer 360)
  ├── Projects       (Active projects, pipeline stages, contract balances)
  ├── Follow-ups     (Urgent, overdue, and upcoming follow-ups)
  ├── Payments       (Commercial receipts, project balances, outstanding amounts)
  ├── Products       (Configured systems and pricing)
  └── Audit Trail    (System audit log)
```

---

## 3. The Unified Customer 360 View

When an operator selects a customer, the screen provides an immediate 360-degree operational overview:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ CUSTOMER: ABC TEXTILE MILLS PVT LTD                 [+ New Project]    │
│ Type: Industrial | City: Coimbatore | Phone: +91 98765 43210            │
├────────────────────────────────────────────────────────────────────────┤
│ Contacts (3)        │ Active Projects (2)         │ Financials         │
│ • R. Sundaram (MD)  │ • 100kW Rooftop Solar       │ • Total Value:     │
│ • K. Murugan (Plant)│   Stage: Installation       │   ₹45,00,000       │
│                     │ • Solar Water Heater        │ • Paid:            │
│                     │   Stage: Site Visit         │   ₹30,00,000       │
│                     │                             │ • Outstanding:     │
│                     │                             │   ₹15,00,000       │
├─────────────────────┴─────────────────────────────┴────────────────────┤
│ Follow-Ups (1 Due Today)   │ Activity & Notes Stream                   │
│ [!] Call regarding phase 2  │ 10:30 AM - Payment ₹10,00,000 received   │
│     inverter delivery      │ Yesterday - Stage moved to Installation   │
└────────────────────────────┴───────────────────────────────────────────┘
```

The operator does not need to navigate away from the customer page to log a note, schedule a follow-up, or see received payments.
