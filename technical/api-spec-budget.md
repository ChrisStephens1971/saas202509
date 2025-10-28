# Budget API Specification

**Version:** 1.0
**Date:** 2025-10-28
**Sprint:** Sprint 9 - Automation and Banking

---

## Overview

The Budget API provides endpoints for creating, managing, and analyzing annual operating budgets for HOAs. It includes budget approval workflows, variance reporting, and budget vs actual analysis.

## Base URL

```
http://localhost:8009/api/v1/accounting/
```

---

## Authentication

All endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. List Budgets

**GET** `/budgets/`

List all budgets for the authenticated tenant.

**Query Parameters:**
- `fiscal_year` (integer, optional) - Filter by fiscal year
- `status` (string, optional) - Filter by status (DRAFT, APPROVED, ACTIVE, CLOSED)
- `fund` (uuid, optional) - Filter by fund ID
- `ordering` (string, optional) - Order by field (e.g., `-fiscal_year`, `start_date`)

**Response:** `200 OK`

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "c2bdc801-10b0-4e4f-9cdd-90fba0d48ff8",
      "name": "FY 2025 Operating Budget",
      "fiscal_year": 2025,
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "fund": "aa119034-54f1-4521-a701-78946223e830",
      "status": "ACTIVE",
      "approved_by": 1,
      "approved_by_name": "Admin User",
      "approved_at": "2025-10-28T07:26:31Z",
      "notes": "Annual operating budget for 2025",
      "created_at": "2025-10-28T07:26:30Z",
      "updated_at": "2025-10-28T07:26:31Z",
      "created_by": 1,
      "created_by_name": "Admin User",
      "lines": [
        {
          "id": "4646437d-d29f-4b5b-97ad-d0480206f8de",
          "account": "a8459fca-dbd5-4194-9648-cc133d7fa529",
          "account_number": "1100",
          "account_name": "Operating Cash",
          "budgeted_amount": "12000.00",
          "notes": "Cash operating budget"
        }
      ],
      "total_budgeted": "72000.00"
    }
  ]
}
```

---

### 2. Create Budget

**POST** `/budgets/`

Create a new budget with budget lines.

**Request Body:**

```json
{
  "name": "FY 2025 Operating Budget",
  "fiscal_year": 2025,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "fund": "aa119034-54f1-4521-a701-78946223e830",
  "notes": "Annual operating budget for 2025",
  "lines": [
    {
      "account": "a8459fca-dbd5-4194-9648-cc133d7fa529",
      "budgeted_amount": "12000.00",
      "notes": "Cash operating budget"
    },
    {
      "account": "d07633dd-e0d1-4dc5-9f05-f3c95d2fd239",
      "budgeted_amount": "36000.00",
      "notes": "Landscaping services"
    }
  ]
}
```

**Response:** `201 Created`

Returns the created budget object (same structure as GET detail).

**Validation Rules:**
- Only one budget per fiscal year per fund (unique constraint)
- At least one budget line required
- All budget lines must reference valid accounts
- Budget amounts must be positive
- Start date must be before end date

---

### 3. Get Budget Detail

**GET** `/budgets/{id}/`

Retrieve a specific budget by ID.

**Response:** `200 OK`

```json
{
  "id": "c2bdc801-10b0-4e4f-9cdd-90fba0d48ff8",
  "name": "FY 2025 Operating Budget",
  "fiscal_year": 2025,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "fund": "aa119034-54f1-4521-a701-78946223e830",
  "status": "ACTIVE",
  "approved_by": 1,
  "approved_by_name": "Admin User",
  "approved_at": "2025-10-28T07:26:31Z",
  "notes": "Annual operating budget for 2025",
  "created_at": "2025-10-28T07:26:30Z",
  "updated_at": "2025-10-28T07:26:31Z",
  "created_by": 1,
  "created_by_name": "Admin User",
  "lines": [...],
  "total_budgeted": "72000.00"
}
```

---

### 4. Update Budget

**PUT** `/budgets/{id}/`
**PATCH** `/budgets/{id}/`

Update an existing budget. Use PUT for full replacement or PATCH for partial updates.

**Request Body:**

```json
{
  "name": "FY 2025 Operating Budget (Revised)",
  "notes": "Updated budget with revised projections"
}
```

**Response:** `200 OK`

Returns the updated budget object.

**Note:** Budget lines cannot be updated via this endpoint. Use the budget lines endpoint directly or delete and recreate the budget.

---

### 5. Delete Budget

**DELETE** `/budgets/{id}/`

Delete a budget and all associated budget lines.

**Response:** `204 No Content`

**Note:** This is a hard delete. Consider implementing a soft delete (status=CLOSED) for production use.

---

### 6. Get Variance Report

**GET** `/budgets/{id}/variance-report/`

Generate a budget vs actual variance report.

**Query Parameters:**
- `as_of_date` (date, optional) - Date to calculate actuals through (default: today)
  - Format: YYYY-MM-DD
  - Must be within budget period

**Response:** `200 OK`

```json
{
  "budget_id": "c2bdc801-10b0-4e4f-9cdd-90fba0d48ff8",
  "budget_name": "FY 2025 Operating Budget",
  "fiscal_year": 2025,
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "as_of_date": "2025-10-28",
  "lines": [
    {
      "account_number": "5100",
      "account_name": "Landscaping Expense",
      "budgeted": "36000.00",
      "actual": "28500.00",
      "variance": "7500.00",
      "variance_pct": "20.8",
      "status": "favorable",
      "notes": "Landscaping services"
    },
    {
      "account_number": "4000",
      "account_name": "Assessment Revenue",
      "budgeted": "150000.00",
      "actual": "155000.00",
      "variance": "5000.00",
      "variance_pct": "3.3",
      "status": "favorable",
      "notes": "Monthly assessments"
    }
  ],
  "totals": {
    "budgeted": "186000.00",
    "actual": "183500.00",
    "variance": "2500.00",
    "variance_pct": "1.3"
  }
}
```

**Variance Status Logic:**
- `on_track` - Within 5% of budget
- `favorable` - For expenses: under budget (positive variance). For revenue: over budget (positive variance)
- `unfavorable` - For expenses: over budget (negative variance). For revenue: under budget (negative variance)

**Variance Calculation:**
- **Expense Accounts:** Variance = Budgeted - Actual (positive = under budget = favorable)
- **Revenue Accounts:** Variance = Actual - Budgeted (positive = over budget = favorable)

---

### 7. Approve Budget

**POST** `/budgets/{id}/approve/`

Approve a draft budget.

**Request Body:** (empty or optional notes)

```json
{
  "notes": "Approved by board on 2025-10-28"
}
```

**Response:** `200 OK`

Returns the updated budget with status=APPROVED and approved_at timestamp.

**Validation:**
- Budget must be in DRAFT status
- User must have approval permissions

---

### 8. Activate Budget

**POST** `/budgets/{id}/activate/`

Activate an approved budget.

**Request Body:** (empty)

**Response:** `200 OK`

Returns the updated budget with status=ACTIVE.

**Validation:**
- Budget must be in APPROVED status
- Only one budget can be active per fiscal year per fund
- Automatically deactivates any other active budgets for the same fiscal year/fund

**Behavior:**
- Sets status to ACTIVE
- Deactivates other ACTIVE budgets for same fiscal year/fund (sets them to APPROVED)

---

### 9. List Budget Lines

**GET** `/budget-lines/`

List all budget lines for the authenticated tenant.

**Query Parameters:**
- `budget` (uuid, optional) - Filter by budget ID

**Response:** `200 OK`

```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "4646437d-d29f-4b5b-97ad-d0480206f8de",
      "account": "a8459fca-dbd5-4194-9648-cc133d7fa529",
      "account_number": "1100",
      "account_name": "Operating Cash",
      "budgeted_amount": "12000.00",
      "notes": "Cash operating budget"
    }
  ]
}
```

---

### 10. Create Budget Line

**POST** `/budget-lines/`

Add a new budget line to an existing budget.

**Request Body:**

```json
{
  "budget": "c2bdc801-10b0-4e4f-9cdd-90fba0d48ff8",
  "account": "a8459fca-dbd5-4194-9648-cc133d7fa529",
  "budgeted_amount": "12000.00",
  "notes": "Cash operating budget"
}
```

**Response:** `201 Created`

Returns the created budget line object.

**Validation:**
- Budget must exist
- Account must exist and belong to the same tenant
- Each account can only appear once per budget (unique constraint)
- Budgeted amount must be positive

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request

```json
{
  "error": "Invalid data provided",
  "details": {
    "fiscal_year": ["This field is required."],
    "lines": ["At least one budget line is required."]
  }
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found

```json
{
  "detail": "Budget not found."
}
```

### 409 Conflict

```json
{
  "error": "A budget for fiscal year 2025 already exists for this fund."
}
```

---

## Data Models

### Budget Status Workflow

```
DRAFT → APPROVED → ACTIVE → CLOSED
  ↓         ↓         ↓
  └─────────┴─────────┘ (can delete at any time)
```

**Status Descriptions:**
- **DRAFT** - Budget is being created/edited. Not yet submitted for approval.
- **APPROVED** - Budget has been approved by authorized user. Ready to be activated.
- **ACTIVE** - Budget is currently in use. Only one budget per fiscal year/fund can be active.
- **CLOSED** - Budget period has ended. Used for historical reference.

### Budget Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Auto | Unique identifier |
| tenant | UUID | Auto | Tenant ID (set from authentication) |
| name | String | Yes | Budget name (e.g., "FY 2025 Operating Budget") |
| fiscal_year | Integer | Yes | Fiscal year (e.g., 2025) |
| start_date | Date | Yes | Budget period start date |
| end_date | Date | Yes | Budget period end date |
| fund | UUID | No | Fund ID (null = all funds) |
| status | String | Auto | Budget status (default: DRAFT) |
| approved_by | Integer | Auto | User ID who approved the budget |
| approved_at | DateTime | Auto | When the budget was approved |
| notes | Text | No | Budget notes and assumptions |
| created_at | DateTime | Auto | Creation timestamp |
| updated_at | DateTime | Auto | Last update timestamp |
| created_by | Integer | Auto | User ID who created the budget |

### Budget Line Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Auto | Unique identifier |
| budget | UUID | Yes | Budget ID |
| account | UUID | Yes | Account ID |
| budgeted_amount | Decimal(12,2) | Yes | Budgeted amount |
| notes | Text | No | Line item notes |

---

## Examples

### Example 1: Create a Complete Budget

```bash
POST /api/v1/accounting/budgets/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "FY 2025 Operating Budget",
  "fiscal_year": 2025,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "fund": "aa119034-54f1-4521-a701-78946223e830",
  "notes": "Annual operating budget approved by board",
  "lines": [
    {
      "account": "d07633dd-e0d1-4dc5-9f05-f3c95d2fd239",
      "budgeted_amount": "36000.00",
      "notes": "Landscaping services - $3,000/month"
    },
    {
      "account": "e8f45abc-1234-5678-90ab-cdef12345678",
      "budgeted_amount": "24000.00",
      "notes": "Pool maintenance - $2,000/month"
    },
    {
      "account": "f9a56bcd-2345-6789-01bc-def234567890",
      "budgeted_amount": "12000.00",
      "notes": "Utilities - $1,000/month"
    }
  ]
}
```

### Example 2: Approve and Activate Budget

```bash
# Step 1: Approve budget
POST /api/v1/accounting/budgets/c2bdc801-10b0-4e4f-9cdd-90fba0d48ff8/approve/
Authorization: Bearer <token>

# Step 2: Activate budget
POST /api/v1/accounting/budgets/c2bdc801-10b0-4e4f-9cdd-90fba0d48ff8/activate/
Authorization: Bearer <token>
```

### Example 3: Get Variance Report for Q1

```bash
GET /api/v1/accounting/budgets/c2bdc801-10b0-4e4f-9cdd-90fba0d48ff8/variance-report/?as_of_date=2025-03-31
Authorization: Bearer <token>
```

---

## Implementation Notes

### Multi-Tenant Security
- All queries automatically filtered by tenant (extracted from JWT token)
- Users can only access budgets for their own tenant
- No cross-tenant data access possible

### Database Constraints
- Unique constraint: `(tenant_id, fiscal_year, fund_id)`
- Unique constraint on budget lines: `(budget_id, account_id)`
- Foreign key constraints ensure referential integrity

### Performance Considerations
- Budget queries use `select_related()` for account lookups
- Variance report queries are optimized with prefetch for journal entries
- Indexes on `(tenant, fiscal_year)` and `(tenant, status)` for fast filtering

### Testing
- Test suite: `backend/accounting/tests/test_budget.py`
- Manual test script: `backend/test_budget_manual.py`
- All tests passing as of 2025-10-28

---

## Related Documentation

- Sprint 9 Plan: `sprints/current/sprint-09-automation-and-banking.md`
- Budget Models: `backend/accounting/models.py` (lines 2088-2290)
- Budget Serializers: `backend/accounting/serializers.py` (lines 191-262)
- Budget Views: `backend/accounting/api_views.py`
- Budget URLs: `backend/accounting/urls.py` (lines 19-20)

---

**Last Updated:** 2025-10-28
**Author:** Claude Code
**Sprint:** Sprint 9 - Automation and Banking
