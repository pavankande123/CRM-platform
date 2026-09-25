# Enermax CRM — Phase 2 API Specification

## 1. API Conventions

* Base Prefix: `/api/v1`
* Authentication: `Authorization: Bearer <JWT_ACCESS_TOKEN>`
* Request Tracking: `X-Request-ID` required or auto-generated.
* Response Format: Standard envelope `StandardResponse[T]` or `StandardResponse[PaginatedResponse[T]]`.
* Error Format: Standard RFC envelope `{ error: { code, message, request_id, details } }`.

---

## 2. API Endpoints Catalog

### Customers & Contacts
* `GET /api/v1/customers` (Query: `page`, `page_size`, `search`, `status`, `customer_type`)
* `POST /api/v1/customers` (Body: Customer details + optional initial primary contact)
* `GET /api/v1/customers/{id}` (Returns customer + contacts + projects + recent activity)
* `PATCH /api/v1/customers/{id}` (Partial update)
* `DELETE /api/v1/customers/{id}` (Soft/hard delete protection)
* `POST /api/v1/customers/{id}/contacts` (Create contact)
* `PATCH /api/v1/contacts/{id}` (Update contact)
* `DELETE /api/v1/contacts/{id}` (Delete contact)

### Products
* `GET /api/v1/products` (Query: `page`, `page_size`, `category`, `is_active`)
* `POST /api/v1/products` (Create product)
* `GET /api/v1/products/{id}` (Product details)
* `PATCH /api/v1/products/{id}` (Update product)

### Flexible Pipelines & Stages
* `GET /api/v1/pipelines` (List tenant pipelines)
* `POST /api/v1/pipelines` (Create pipeline with ordered stages)
* `GET /api/v1/pipelines/{id}` (Pipeline details + stages)
* `POST /api/v1/pipelines/{id}/stages` (Add stage)

### Projects & Stage Transition
* `GET /api/v1/projects` (Query: `page`, `page_size`, `customer_id`, `stage_id`, `status`)
* `POST /api/v1/projects` (Create project with customer, product, pipeline, initial stage, value)
* `GET /api/v1/projects/{id}` (Full project details, customer info, stage history, payments summary)
* `PATCH /api/v1/projects/{id}` (Update project metadata)
* `POST /api/v1/projects/{id}/stage` (Move project to a new stage with transactional history entry)

### Follow-ups
* `GET /api/v1/follow-ups` (Query: `status`, `overdue_only`, `today_only`, `customer_id`, `project_id`)
* `POST /api/v1/follow-ups` (Schedule follow-up)
* `PATCH /api/v1/follow-ups/{id}/complete` (Mark complete with notes)
* `PATCH /api/v1/follow-ups/{id}/cancel` (Cancel follow-up)

### Payments
* `GET /api/v1/payments` (Query: `customer_id`, `project_id`, `status`)
* `POST /api/v1/payments` (Record payment with project, amount, reference number)
* `GET /api/v1/payments/summary` (Aggregate project values, total received, total outstanding)

### Notes & Document Metadata
* `POST /api/v1/notes` (Attach note to customer, project, follow-up, or payment)
* `GET /api/v1/notes` (Query: `customer_id`, `project_id`)
* `POST /api/v1/documents` (Record document metadata: quotation, invoice, spec)
* `GET /api/v1/documents` (Query: `customer_id`, `project_id`)

### Search & Dashboard
* `GET /api/v1/search?q={query}` (Global multi-entity search)
* `GET /api/v1/dashboard` (Real-time operational business metrics and counts)
