# Sprint 16 - Architectural Review Committee (ARC) Workflow

**Sprint Duration:** TBD (2 weeks estimated)
**Sprint Goal:** Implement ARC workflow for homeowner architectural modification requests with approval tracking and compliance verification
**Status:** Planning

---

## Sprint Goal

Build an Architectural Review Committee (ARC) workflow system that enables homeowners to submit modification requests (paint, fencing, landscaping, additions) with documentation, allows board/committee review and approval, tracks conditions, and verifies completion. This prevents unauthorized modifications and provides permanent records for property history.

Key features:
- Owner self-service request submission portal
- Document upload (plans, specs, contractor info)
- Multi-reviewer approval workflow
- Conditional approval tracking
- Completion verification with photos
- Permanent record for resale disclosures

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
| US-164 | Backend: ARC models (Request, RequestType, Approval) | M | Chris | 📋 Todo | Core data models |
| US-165 | Backend: Document upload and storage | M | Chris | 📋 Todo | Plans, specs, photos |
| US-166 | Backend: ARC API endpoints (CRUD + workflow) | L | Chris | 📋 Todo | REST API |
| US-167 | Frontend: ARC requests list page | S | Chris | 📋 Todo | Board view |
| US-168 | Frontend: Submit ARC request form (owner portal) | L | Chris | 📋 Todo | Owner self-service |
| US-169 | Frontend: Review and approve request page | M | Chris | 📋 Todo | Committee workflow |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-170 | Backend: Multi-reviewer approval workflow | M | Chris | 📋 Todo | Committee voting |
| US-171 | Frontend: Request detail page with timeline | M | Chris | 📋 Todo | Status tracking |
| US-172 | Email notifications for status changes | S | Chris | 📋 Todo | Owner alerts |
| US-173 | Frontend: Completion verification form | S | Chris | 📋 Todo | Inspector checklist |

### Low Priority (Nice to Have)

| Story | Description | Estimate | Assignee | Status | Notes |
|-------|-------------|----------|----------|--------|-------|
| US-174 | Request templates (common modifications) | S | Chris | 📋 Todo | Pre-filled forms |
| US-175 | Conditional approval tracking | M | Chris | 📋 Todo | "Approved if..." |
| US-176 | ARC statistics dashboard | S | Chris | 📋 Todo | Analytics |

**Story Status Legend:**
- 📋 Todo
- 🏗️ In Progress
- 👀 In Review
- ✅ Done
- ❌ Blocked

---

## Technical Design

### Backend Models

**ARCRequestType:**
- code: str (e.g., "PAINT", "FENCE", "LANDSCAPE", "ADDITION")
- name: str (e.g., "Exterior Paint", "Fence Installation")
- description: text
- requires_plans: bool (does it need architectural drawings?)
- requires_contractor: bool (must provide contractor info?)
- typical_review_days: int (e.g., 30 days)
- is_active: bool

**ARCRequest:**
- tenant: FK(Tenant)
- unit: FK(Unit)
- owner: FK(Owner)
- request_type: FK(ARCRequestType)
- status: str (Draft, Submitted, Under Review, Approved, Denied, Approved with Conditions, Completed, Cancelled)
- title: str (e.g., "Repaint House - Blue to Gray")
- description: text (detailed proposal)
- requested_start_date: DATE
- estimated_completion_date: DATE
- contractor_name: str (nullable)
- contractor_license: str (nullable)
- contractor_phone: str (nullable)
- submitted_at: TIMESTAMPTZ (nullable)
- reviewed_at: TIMESTAMPTZ (nullable)
- completed_at: TIMESTAMPTZ (nullable)
- created_by: FK(User) (owner who submitted)

**ARCDocument:**
- request: FK(ARCRequest)
- document_type: str (Plan, Spec, Photo, Contract, Other)
- file_url: str (S3 path or local storage)
- file_name: str
- file_size: int (bytes)
- uploaded_at: TIMESTAMPTZ
- uploaded_by: FK(User)

**ARCReview:**
- request: FK(ARCRequest)
- reviewer: FK(User) (committee member)
- review_date: TIMESTAMPTZ
- decision: str (Approve, Deny, Request Changes, Abstain)
- comments: text
- conditions: text (nullable - "Approved if fence is white, not black")

**ARCApproval:**
- request: FK(ARCRequest)
- final_decision: str (Approved, Denied, Approved with Conditions)
- decision_date: DATE
- conditions: text (nullable)
- expiration_date: DATE (approval expires if not started)
- approved_by: FK(User) (final approver, usually board president)
- board_resolution: str (nullable - resolution number if required)

**ARCCompletion:**
- request: FK(ARCRequest)
- inspected_by: FK(User)
- inspection_date: DATE
- complies_with_approval: bool
- inspector_notes: text
- photo_url: str (completion photo)

### API Endpoints

**Request Types:**
- GET /api/arc-request-types/ - List all types
- POST /api/arc-request-types/ - Create type (admin only)
- PUT /api/arc-request-types/{id}/ - Update type

**Requests:**
- GET /api/arc-requests/ - List all requests (filters: status, unit, date)
- POST /api/arc-requests/ - Create draft request (owner)
- GET /api/arc-requests/{id}/ - Get request detail
- PUT /api/arc-requests/{id}/ - Update request (before submission)
- POST /api/arc-requests/{id}/submit/ - Submit for review
- DELETE /api/arc-requests/{id}/ - Cancel request

**Documents:**
- POST /api/arc-requests/{id}/documents/ - Upload document
- GET /api/arc-requests/{id}/documents/ - List documents
- DELETE /api/arc-requests/{id}/documents/{doc_id}/ - Delete document

**Review:**
- POST /api/arc-requests/{id}/reviews/ - Submit review (committee member)
- GET /api/arc-requests/{id}/reviews/ - Get all reviews
- POST /api/arc-requests/{id}/approve/ - Final approval (board)
- POST /api/arc-requests/{id}/deny/ - Final denial (board)

**Completion:**
- POST /api/arc-requests/{id}/complete/ - Mark as completed (inspector)
- POST /api/arc-requests/{id}/verify/ - Verify completion

### Frontend Pages

**ARCRequestsListPage (Board View):**
- Table view of all requests
- Filters: Status, Request type, Date range
- Search by address or owner name
- Status badges (color-coded)
- Quick actions: Approve, Deny, View details

**SubmitARCRequestPage (Owner Portal):**
- Form wizard (multi-step):
  - Step 1: Request type selection
  - Step 2: Details and description
  - Step 3: Contractor information
  - Step 4: Document upload (plans, photos)
  - Step 5: Review and submit
- Preview mode before submission
- Save as draft (continue later)

**ARCRequestDetailPage:**
- Request header (unit, type, status, dates)
- Description and details
- Document gallery (plans, specs, photos)
- Contractor information
- Review timeline (who reviewed, when, decision)
- Approval/denial display
- Action buttons (based on status and role):
  - Submit review (committee member)
  - Approve/Deny (board)
  - Mark complete (inspector)
  - Cancel (owner, if not yet reviewed)

**ReviewRequestPage (Committee View):**
- Request details (read-only)
- Document viewer
- Review form:
  - Decision: Approve / Deny / Request Changes
  - Comments (required)
  - Conditions (if approved with conditions)
- Submit review button

**Components:**
- ARCRequestCard: Summary card for list view
- RequestTimeline: Visual workflow with progress
- DocumentGallery: Plans and photos display
- ReviewForm: Committee review interface
- ApprovalBadge: Status indicator

---

## Workflow States

### Request Lifecycle

```
Draft → Submitted → Under Review → Approved/Denied → Completed
                                 ↘ Approved with Conditions → Completed
```

**Draft:**
- Owner creating request
- Can save and edit
- Not visible to committee

**Submitted:**
- Owner submitted for review
- Visible to committee
- Cannot be edited by owner

**Under Review:**
- One or more committee members reviewing
- Comments and questions allowed
- Owner can respond to questions

**Approved:**
- Committee approved without conditions
- Owner can proceed
- Expiration date set (typically 12 months)

**Approved with Conditions:**
- Approved BUT owner must meet conditions
- Conditions documented (e.g., "fence must be white")
- Inspection required upon completion

**Denied:**
- Committee denied request
- Reason required
- Owner can appeal or resubmit with changes

**Completed:**
- Work finished
- Inspector verified compliance
- Permanent record created

**Cancelled:**
- Owner cancelled request
- Or expired (not started within 12 months)

---

## Multi-Reviewer Logic

**Option 1: Unanimous Approval Required**
- All committee members must approve
- One "deny" = request denied
- Simple but strict

**Option 2: Majority Vote**
- 3+ reviewers required
- Majority approve = approved
- More flexible

**MVP Decision: Simple Single Approver**
- One designated committee chair or board president
- Other committee members can comment
- Only chair can approve/deny
- Simplifies workflow for MVP

---

## Integration Requirements

### Email Notifications

Send email at each status change:

**Owner receives:**
- Confirmation: "Your request has been submitted"
- Under review: "Your request is being reviewed"
- Approved: "Your request has been approved - see conditions"
- Denied: "Your request has been denied - see reason"
- Expiring: "Your approval expires in 30 days"

**Committee receives:**
- New submission: "New ARC request requires review"
- Comment added: "Owner responded to your question"

### Document Storage

- Local filesystem for MVP (organize by tenant/request)
- S3 for production (scalable, durable)
- Max file size: 25MB per file
- Supported formats: PDF, JPG, PNG, DWG (AutoCAD)
- Retention: Permanent (needed for resale disclosures)

### Violation Integration (Future)

- Unapproved modifications → Automatic violation
- If work starts without ARC approval → Flag as violation
- Connects to Sprint 15 (Violation Tracking)

---

## Technical Debt / Maintenance

- [ ] Add document versioning (owner uploads revised plans)
- [ ] Implement expiration alerts (approval expires in 30 days)
- [ ] Add appeal workflow (owner can appeal denial)
- [ ] Consider role-based permissions (committee vs board)

---

## Definition of Done

- [ ] All models created with migrations
- [ ] All API endpoints implemented and tested
- [ ] Frontend pages functional with real data
- [ ] Document upload working (PDF, images)
- [ ] Email notifications sent on status changes
- [ ] Approval workflow functional (submit → review → approve)
- [ ] TypeScript compiles without errors
- [ ] Feature demonstrated in UI

---

## Links & References

- Related Roadmap: `product/roadmap/2025-2027-hoa-accounting-roadmap.md` (Phase 3)
- Pain Point: `product/HOA-PAIN-POINTS-AND-REQUIREMENTS.md` (Pain Point #5)
- Legal reference: ARC authority under Davis-Stirling Act (California)
- Industry standard: CAI Architectural Review Process Guidelines

---

## Success Metrics

**MVP Success Criteria:**
- 10+ ARC requests submitted in pilot HOA
- 100% of requests reviewed within 30 days
- 0 unauthorized modifications (all go through ARC)
- Document retention working (permanent records)
- Board reports "easier to track modifications" in feedback

---

## Notes

**Common Request Types:**
1. **Exterior Paint:** Most common, usually approved quickly
2. **Fencing:** Requires plans, height/material restrictions
3. **Landscaping:** Trees, shrubs, hardscaping
4. **Solar Panels:** Increasingly common, legal restrictions on denial
5. **Room Additions:** Complex, requires architectural plans
6. **Windows/Doors:** Style and color restrictions
7. **Roofing:** Material and color matching

**Legal Considerations:**
- **Solar Rights:** California law limits HOA ability to deny solar panels
- **Reasonable Restrictions:** HOAs can't be arbitrary or discriminatory
- **Timeliness:** Many states require response within 30-60 days
- **Documentation:** Permanent records protect both owner and HOA

**Owner Portal Integration:**
- ARC request submission available in owner portal
- Status tracking visible to owner
- Document download (approved plans for contractor)
- Completion photos upload (owner can self-report completion)

**Future Enhancements (Post-Sprint):**
- Recurring approvals (same request type, multiple owners)
- Template library (pre-approved paint colors, fence styles)
- Integration with architectural guidelines (auto-deny if violates rules)
- Property history report (all modifications over time)
