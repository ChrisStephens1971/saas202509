# Sprint 15 - Violation Tracking System

**Sprint Duration:** TBD (2 weeks estimated)
**Sprint Goal:** Implement comprehensive violation tracking with photo evidence, escalation workflow, and fine automation
**Status:** Planning

---

## Sprint Goal

Build a violation tracking system that enables HOAs to consistently enforce community rules with documented evidence, automated escalation, and fine integration with the accounting ledger. This addresses a critical HOA need: protecting boards from selective enforcement lawsuits while automating fine collection.

Key features:
- Violation creation with photo evidence
- Multi-step escalation workflow (courtesy → warning → fine → legal)
- Fine schedules per violation type
- Automatic posting of fines to owner ledgers
- Evidence preservation with timestamps and GPS coordinates

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
| US-151 | Backend: Violation models (Violation, ViolationType, FineSchedule) | M | Chris | 📋 Todo | Core data models |
| US-152 | Backend: Photo upload and storage (S3 or local) | M | Chris | 📋 Todo | Evidence storage |
| US-153 | Backend: Violation API endpoints (CRUD) | M | Chris | 📋 Todo | REST API |
| US-154 | Frontend: Violations list page with filters | S | Chris | 📋 Todo | Table view |
| US-155 | Frontend: Create violation form with photo upload | L | Chris | 📋 Todo | Multi-step form |
| US-156 | Backend: Fine calculation and posting to ledger | L | Chris | 📋 Todo | Accounting integration |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-157 | Backend: Escalation workflow automation | M | Chris | 📋 Todo | Step tracking |
| US-158 | Frontend: Violation detail page with timeline | M | Chris | 📋 Todo | Evidence display |
| US-159 | Frontend: Fine schedule configuration UI | S | Chris | 📋 Todo | Admin settings |
| US-160 | Email notifications for violation notices | S | Chris | 📋 Todo | Owner communication |

### Low Priority (Nice to Have)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-161 | Mobile inspector app POC (responsive web) | M | Chris | 📋 Todo | Field entry |
| US-162 | GPS coordinate capture from mobile | S | Chris | 📋 Todo | Location tracking |
| US-163 | Violation statistics dashboard | S | Chris | 📋 Todo | Analytics |

**Story Status Legend:**
- 📋 Todo
- 🏗️ In Progress
- 👀 In Review
- ✅ Done
- ❌ Blocked

---

## Technical Design

### Backend Models

**ViolationType:**
- code: str (e.g., "LAND-001", "PARK-002")
- name: str (e.g., "Overgrown Lawn", "Unauthorized Parking")
- description: text
- category: str (Landscaping, Parking, Noise, Structural, etc.)
- is_active: bool

**FineSchedule:**
- violation_type: FK(ViolationType)
- step_number: int (1-5)
- step_name: str (Courtesy, Warning, Fine, Continued, Legal)
- days_after_previous: int (e.g., 7 days)
- fine_amount: Decimal (e.g., $50.00)
- description: text
- requires_board_approval: bool

**Violation:**
- tenant: FK(Tenant)
- unit: FK(Unit)
- owner: FK(Owner)
- violation_type: FK(ViolationType)
- status: str (Open, Cured, Fined, Legal, Closed)
- current_step: int (1-5)
- discovered_date: DATE
- due_date: DATE (deadline to cure)
- cured_date: DATE (nullable)
- description: text
- inspector_notes: text
- created_by: FK(User)
- created_at: TIMESTAMPTZ

**ViolationEvidence:**
- violation: FK(Violation)
- photo_url: str (S3 path or local storage)
- caption: str
- taken_at: TIMESTAMPTZ
- latitude: Decimal (nullable)
- longitude: Decimal (nullable)
- uploaded_by: FK(User)

**ViolationEscalation:**
- violation: FK(Violation)
- step_number: int
- step_name: str
- escalated_at: TIMESTAMPTZ
- fine_amount: Decimal (if applicable)
- notice_sent: bool
- notice_sent_at: TIMESTAMPTZ (nullable)
- notice_method: str (Email, Certified Mail, Hand Delivered)
- tracking_number: str (for certified mail)
- notes: text

**ViolationFine:**
- violation: FK(Violation)
- escalation: FK(ViolationEscalation)
- invoice: FK(Invoice) (link to accounting)
- journal_entry: FK(JournalEntry) (link to GL)
- amount: Decimal
- posted_date: DATE
- paid_date: DATE (nullable)
- status: str (Pending, Posted, Paid, Waived)

### API Endpoints

**Violation Types:**
- GET /api/violation-types/ - List all types
- POST /api/violation-types/ - Create type (admin only)
- PUT /api/violation-types/{id}/ - Update type
- DELETE /api/violation-types/{id}/ - Deactivate type

**Fine Schedules:**
- GET /api/fine-schedules/?violation_type={id} - Get schedule
- POST /api/fine-schedules/ - Create schedule
- PUT /api/fine-schedules/{id}/ - Update schedule

**Violations:**
- GET /api/violations/ - List all violations (filters: status, unit, date range)
- POST /api/violations/ - Create violation
- GET /api/violations/{id}/ - Get violation detail
- PUT /api/violations/{id}/ - Update violation
- POST /api/violations/{id}/escalate/ - Move to next step
- POST /api/violations/{id}/cure/ - Mark as cured
- POST /api/violations/{id}/waive-fine/ - Waive fine (requires approval)

**Evidence:**
- POST /api/violations/{id}/evidence/ - Upload photo
- GET /api/violations/{id}/evidence/ - List evidence
- DELETE /api/violations/{id}/evidence/{photo_id}/ - Delete photo

**Integration:**
- POST /api/violations/{id}/post-fine/ - Post fine to owner ledger

### Frontend Pages

**ViolationsListPage:**
- Table view of all violations
- Filters: Status, Unit, Date range, Violation type
- Search by address or owner name
- Create violation button
- Export to CSV

**CreateViolationPage:**
- Form fields: Unit, Violation type, Description, Due date
- Photo upload (drag-and-drop, multiple files)
- GPS coordinate capture (if mobile)
- Inspector notes
- Submit button (creates violation and sends courtesy notice)

**ViolationDetailPage:**
- Violation header (unit, type, status)
- Photo gallery (evidence)
- Escalation timeline (visual steps)
- Current step indicator
- Action buttons:
  - Mark as cured
  - Escalate to next step
  - Waive fine (admin only)
  - Add notes
- History log (all actions with timestamps)

**Components:**
- ViolationCard: Summary card for list view
- EscalationTimeline: Visual workflow with progress
- PhotoGallery: Evidence display with zoom
- FineScheduleEditor: Admin configuration UI

---

## Integration Requirements

### Accounting Integration

When fine is posted (US-156):
1. Create Invoice record linked to owner/unit
2. Create JournalEntry:
   - Debit: Accounts Receivable (1200) - $50.00
   - Credit: Violation Fee Revenue (4500) - $50.00
3. Link ViolationFine to Invoice and JournalEntry
4. Update owner ledger balance

### Email Notifications

Violation notices sent via existing EmailService:
- Courtesy notice: "You have a violation - please cure by {due_date}"
- Warning notice: "Final warning - cure by {due_date} or fine will be assessed"
- Fine notice: "Fine of ${amount} has been posted to your account"
- Include: Photos, description, cure instructions, contact info

---

## Technical Debt / Maintenance

- [ ] Add photo compression to reduce storage costs
- [ ] Implement photo retention policy (delete after X years?)
- [ ] Add role-based access control (inspector vs admin)
- [ ] Consider compliance with state laws (notice requirements vary)

---

## Definition of Done

- [ ] All models created with migrations
- [ ] All API endpoints implemented and tested
- [ ] Frontend pages functional with real data
- [ ] Photo upload working (local storage for MVP, S3 later)
- [ ] Fine posting to ledger working correctly
- [ ] Email notifications sent on escalation
- [ ] TypeScript compiles without errors
- [ ] Feature demonstrated in UI

---

## Links & References

- Related Roadmap: `product/roadmap/2025-2027-hoa-accounting-roadmap.md` (Phase 3)
- Pain Point: `product/HOA-PAIN-POINTS-AND-REQUIREMENTS.md` (Pain Point #5)
- Accounting architecture: `technical/architecture/MULTI-TENANT-ACCOUNTING-ARCHITECTURE.md`
- Legal reference: Selective enforcement case law (Davis v. Huey, CA Supreme Court)

---

## Success Metrics

**MVP Success Criteria:**
- 20+ violations created in pilot HOA
- 100% of fines posted correctly to owner ledgers
- 0 selective enforcement complaints
- Evidence photos preserved with timestamps
- Board reports "more consistent enforcement" in feedback

---

## Notes

**Mobile-First Consideration:**
- Inspector walks property with tablet/phone
- Responsive web app (not native mobile initially)
- GPS and camera access via browser APIs
- Offline support not required for MVP

**Legal Compliance:**
- Notice requirements vary by state
- California: 10 days to cure before fine
- Florida: 14 days for first offense
- Texas: Varies by CC&Rs
- System should support configurable notice periods

**Future Enhancements (Post-Sprint):**
- Bulk violation import (mass enforcement)
- Recurring violations (e.g., parking violations every week)
- Owner portal view (see violations and cure status)
- Integration with ARC (violations from unapproved changes)
