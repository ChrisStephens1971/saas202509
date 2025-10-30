# Sprint 17 - Work Order System with Vendor Management

**Sprint Duration:** TBD (2 weeks estimated)
**Sprint Goal:** Implement work order and vendor management system with cost tracking and GL integration
**Status:** Planning

---

## Sprint Goal

Build a work order system that enables HOAs to track maintenance requests, assign work to vendors or staff, monitor completion, and automatically code expenses to the correct general ledger accounts. This creates financial accountability for all operational spending and provides a complete audit trail from request to payment.

Key features:
- Work order creation (from residents or proactive maintenance)
- Vendor directory and assignment
- Priority and status tracking
- Cost estimation and actual cost capture
- GL account coding for expenses
- Invoice matching (link vendor invoice to work order)

---

## Sprint Capacity

**Available Days:** 10 working days
**Capacity:** 60-80 hours
**Commitments/Time Off:** None

---

## Sprint Backlog

### High Priority (Must Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-177 | Backend: Work order models (WorkOrder, Vendor, Category) | M | Chris | 📋 Todo | Core data models |
| US-178 | Backend: Work order API endpoints (CRUD) | M | Chris | 📋 Todo | REST API |
| US-179 | Backend: Vendor directory models and API | M | Chris | 📋 Todo | Vendor management |
| US-180 | Frontend: Work orders list page with filters | S | Chris | 📋 Todo | Board/manager view |
| US-181 | Frontend: Create work order form | M | Chris | 📋 Todo | Request entry |
| US-182 | Backend: Cost tracking and GL account mapping | L | Chris | 📋 Todo | Accounting integration |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-183 | Frontend: Work order detail page with timeline | M | Chris | 📋 Todo | Status tracking |
| US-184 | Frontend: Vendor directory page | S | Chris | 📋 Todo | Vendor list |
| US-185 | Frontend: Owner portal - submit work request | M | Chris | 📋 Todo | Resident self-service |
| US-186 | Email notifications for status changes | S | Chris | 📋 Todo | Vendor and owner alerts |

### Low Priority (Nice to Have)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-187 | Recurring maintenance schedules | M | Chris | 📋 Todo | Preventive maintenance |
| US-188 | Work order statistics dashboard | S | Chris | 📋 Todo | Analytics |
| US-189 | Vendor performance tracking | M | Chris | 📋 Todo | Rating system |
| US-190 | Photo upload for completed work | S | Chris | 📋 Todo | Evidence |

**Story Status Legend:**
- 📋 Todo
- 🏗️ In Progress
- 👀 In Review
- ✅ Done
- ❌ Blocked

---

## Technical Design

### Backend Models

**WorkOrderCategory:**
- code: str (e.g., "LAND", "POOL", "HVAC", "PLUMB")
- name: str (e.g., "Landscaping", "Pool Maintenance")
- description: text
- default_gl_account: FK(GLAccount) (for expense coding)
- is_active: bool

**Vendor:**
- tenant: FK(Tenant)
- name: str (company name)
- contact_name: str
- phone: str
- email: str
- address: text
- tax_id: str (EIN for 1099 reporting)
- license_number: str (nullable)
- insurance_expiration: DATE (nullable)
- payment_terms: str (Net 30, Due on Receipt, etc.)
- specialty: str (category they serve)
- is_active: bool
- notes: text
- created_at: TIMESTAMPTZ

**WorkOrder:**
- tenant: FK(Tenant)
- work_order_number: str (auto-generated, e.g., "WO-2025-001")
- category: FK(WorkOrderCategory)
- title: str (e.g., "Repair Pool Pump")
- description: text (detailed problem/task description)
- priority: str (Emergency, High, Medium, Low)
- status: str (Draft, Open, Assigned, In Progress, Completed, Closed, Cancelled)
- location: str (unit number, common area description)
- unit: FK(Unit) (nullable - if unit-specific)
- requested_by: FK(User) (owner or staff)
- assigned_to_vendor: FK(Vendor) (nullable)
- assigned_to_staff: FK(User) (nullable)
- estimated_cost: Decimal (nullable)
- actual_cost: Decimal (nullable)
- gl_account: FK(GLAccount) (expense account code)
- fund: FK(Fund) (operating, reserve, or special assessment)
- requested_date: DATE
- scheduled_date: DATE (nullable)
- completed_date: DATE (nullable)
- created_by: FK(User)
- created_at: TIMESTAMPTZ

**WorkOrderComment:**
- work_order: FK(WorkOrder)
- comment: text
- commented_by: FK(User)
- commented_at: TIMESTAMPTZ
- is_internal: bool (visible to staff only, or visible to requester?)

**WorkOrderAttachment:**
- work_order: FK(WorkOrder)
- file_url: str (S3 path or local storage)
- file_name: str
- uploaded_by: FK(User)
- uploaded_at: TIMESTAMPTZ

**WorkOrderInvoice:**
- work_order: FK(WorkOrder)
- vendor: FK(Vendor)
- invoice_number: str
- invoice_date: DATE
- amount: Decimal
- payment_status: str (Pending, Approved, Paid)
- journal_entry: FK(JournalEntry) (link to GL)
- approved_by: FK(User)
- approved_at: TIMESTAMPTZ (nullable)

### API Endpoints

**Categories:**
- GET /api/work-order-categories/ - List all categories
- POST /api/work-order-categories/ - Create category (admin only)
- PUT /api/work-order-categories/{id}/ - Update category

**Vendors:**
- GET /api/vendors/ - List all vendors
- POST /api/vendors/ - Create vendor
- GET /api/vendors/{id}/ - Get vendor detail
- PUT /api/vendors/{id}/ - Update vendor
- DELETE /api/vendors/{id}/ - Deactivate vendor

**Work Orders:**
- GET /api/work-orders/ - List all work orders (filters: status, category, date)
- POST /api/work-orders/ - Create work order
- GET /api/work-orders/{id}/ - Get work order detail
- PUT /api/work-orders/{id}/ - Update work order
- POST /api/work-orders/{id}/assign/ - Assign to vendor/staff
- POST /api/work-orders/{id}/complete/ - Mark as completed
- POST /api/work-orders/{id}/close/ - Close work order
- DELETE /api/work-orders/{id}/ - Cancel work order

**Comments:**
- POST /api/work-orders/{id}/comments/ - Add comment
- GET /api/work-orders/{id}/comments/ - List comments

**Attachments:**
- POST /api/work-orders/{id}/attachments/ - Upload attachment
- GET /api/work-orders/{id}/attachments/ - List attachments
- DELETE /api/work-orders/{id}/attachments/{file_id}/ - Delete attachment

**Invoice Matching:**
- POST /api/work-orders/{id}/invoices/ - Link invoice to work order
- POST /api/work-orders/{id}/invoices/{invoice_id}/approve/ - Approve invoice for payment

### Frontend Pages

**WorkOrdersListPage:**
- Table view of all work orders
- Filters: Status, Category, Priority, Date range
- Search by work order number or description
- Color-coded priority badges
- Create work order button
- Export to CSV

**CreateWorkOrderPage:**
- Form fields:
  - Category (dropdown)
  - Title (short description)
  - Description (detailed problem)
  - Priority (Emergency/High/Medium/Low)
  - Location (unit or common area)
  - Requested by (owner or staff)
  - Estimated cost (optional)
  - GL account (auto-populated from category)
  - Fund (operating/reserve)
- Photo upload (attach photos of problem)
- Submit button

**WorkOrderDetailPage:**
- Work order header (number, category, priority, status)
- Description and details
- Assignment information (vendor or staff)
- Cost tracking (estimated vs actual)
- GL account and fund
- Comments timeline
- Attachments (photos, documents)
- Action buttons (based on status and role):
  - Assign to vendor
  - Mark in progress
  - Mark completed
  - Close work order
  - Add comment
  - Upload attachment

**VendorDirectoryPage:**
- List of all vendors
- Filter by specialty
- Search by name
- Vendor cards with contact info
- Add vendor button
- Edit/deactivate actions

**VendorDetailPage:**
- Vendor information (name, contact, license)
- Work order history (all WOs for this vendor)
- Total spent (sum of all invoices)
- Average completion time
- Performance notes

**SubmitWorkRequestPage (Owner Portal):**
- Simplified form for owners:
  - Problem description
  - Location (auto-filled to their unit)
  - Priority (owner selects)
  - Photo upload (show the problem)
- Submit button (creates work order, notifies management)

**Components:**
- WorkOrderCard: Summary card for list view
- StatusTimeline: Visual workflow with progress
- VendorSelector: Dropdown with vendor search
- CostTracker: Estimated vs actual display
- GLAccountPicker: Account selection with search

---

## Workflow States

### Work Order Lifecycle

```
Draft → Open → Assigned → In Progress → Completed → Closed
           ↓
        Cancelled
```

**Draft:**
- Being created, not yet submitted
- Can be edited or deleted

**Open:**
- Submitted, awaiting assignment
- Visible to management

**Assigned:**
- Assigned to vendor or staff
- Vendor notified
- Scheduled date set

**In Progress:**
- Work actively being done
- Vendor can update status and add comments

**Completed:**
- Work finished
- Invoice submitted (if vendor)
- Cost captured

**Closed:**
- Invoice paid
- Final status
- Permanent record

**Cancelled:**
- Work order cancelled (no longer needed)
- Reason required

---

## Priority Levels

**Emergency:**
- Examples: Water leak, no heat in winter, electrical hazard
- Response time: 4 hours
- Notification: Immediate alert to management and on-call vendor

**High:**
- Examples: Broken pool equipment, gate not working, major landscaping issue
- Response time: 24 hours
- Notification: Email to management

**Medium:**
- Examples: Light bulb replacement, minor landscaping, routine maintenance
- Response time: 3 days
- Notification: Daily digest

**Low:**
- Examples: Cosmetic issues, non-urgent improvements
- Response time: 1 week
- Notification: Weekly summary

---

## Integration Requirements

### Accounting Integration (US-182)

When work order is completed and invoice approved:

1. **Create JournalEntry:**
   ```
   Debit:  Landscaping Expense (5100) - $500.00
   Credit: Accounts Payable (2100) - $500.00
   ```

2. **Link WorkOrderInvoice to JournalEntry**
   - WorkOrderInvoice.journal_entry = JournalEntry.id
   - WorkOrder.actual_cost = Invoice.amount

3. **Fund allocation:**
   - Operating work orders → Operating Fund
   - Capital projects (roof, pavement) → Reserve Fund
   - Special projects → Special Assessment Fund

4. **GL account mapping:**
   - Category determines default account
   - Manager can override if needed
   - Examples:
     - Landscaping → 5100 (Landscaping Expense)
     - Pool Maintenance → 5350 (Pool/Spa Expense)
     - Plumbing → 5200 (Repairs & Maintenance)
     - HVAC → 5210 (HVAC Maintenance)

### Email Notifications

**Owner receives (if they submitted):**
- Confirmation: "Your work request has been received"
- Assigned: "A vendor has been assigned to your request"
- Completed: "Your work request has been completed"

**Vendor receives:**
- Assignment: "You have been assigned work order #WO-2025-001"
- Updates: "Owner added a comment to your work order"

**Management receives:**
- New request: "New work request from owner"
- Completed: "Work order completed, ready for review"
- Over budget: "Work order cost exceeds estimate by $X"

### Owner Portal Integration

- Owners can view their submitted work orders
- Status tracking (real-time updates)
- Communication with management (comments)
- Photo upload (show the problem)
- Completion notification

---

## Technical Debt / Maintenance

- [ ] Add work order templates (common maintenance tasks)
- [ ] Implement recurring maintenance schedules
- [ ] Add vendor insurance tracking with expiration alerts
- [ ] Consider role-based access (vendor portal for updates)
- [ ] Add cost approval workflow (require board approval over $X)

---

## Definition of Done

- [ ] All models created with migrations
- [ ] All API endpoints implemented and tested
- [ ] Frontend pages functional with real data
- [ ] Vendor directory working
- [ ] Work order creation and assignment working
- [ ] GL account coding functional
- [ ] Invoice matching creates journal entries correctly
- [ ] Email notifications sent on status changes
- [ ] TypeScript compiles without errors
- [ ] Feature demonstrated in UI

---

## Links & References

- Related Roadmap: `product/roadmap/2025-2027-hoa-accounting-roadmap.md` (Phase 3)
- Pain Point: `product/HOA-PAIN-POINTS-AND-REQUIREMENTS.md` (Pain Point #5)
- Accounting architecture: `technical/architecture/MULTI-TENANT-ACCOUNTING-ARCHITECTURE.md`
- GL accounts: Reference existing chart of accounts for expense categories

---

## Success Metrics

**MVP Success Criteria:**
- 30+ work orders created in pilot HOA
- 100% of completed work orders coded to GL
- Average response time <24 hours for high priority
- 80%+ owner satisfaction with work request process
- Board reports "better vendor tracking" in feedback

---

## Notes

**Common Work Order Categories:**
1. **Landscaping:** Mowing, trimming, irrigation, tree removal
2. **Pool/Spa:** Pump repair, cleaning, chemical balance
3. **Building Maintenance:** Painting, repairs, cleaning
4. **Plumbing:** Leaks, clogs, pipe repairs
5. **Electrical:** Lighting, outlets, circuit issues
6. **HVAC:** Heating, cooling, ventilation
7. **Security:** Gate repairs, lock changes, camera issues
8. **Pest Control:** Regular service, emergency treatment

**Vendor Management Best Practices:**
- Collect W-9 for tax reporting
- Verify insurance annually
- Check license status
- Track performance (on-time, quality, cost)
- Maintain contact list for emergencies

**Future Enhancements (Post-Sprint):**
- Preventive maintenance scheduling (quarterly pool service, annual HVAC)
- Vendor bidding (multiple vendors quote on work order)
- Warranty tracking (equipment under warranty)
- Asset management integration (link work orders to assets like pool pump)
- Mobile app for vendors (update status from field)

**Integration with Other Modules:**
- Violation → Work Order: "Fix this violation" creates work order
- ARC → Work Order: "Complete approved modification" creates work order
- Reserve Planning → Work Order: "Schedule roof replacement" creates capital work order
