# Sprint 19 - Violation Tracking System

**Sprint Duration:** 2025-10-29
**Sprint Goal:** Track violations with photo evidence and compliance workflow
**Status:** Active

## Sprint Goal

Build violation tracking system for HOA compliance:
- Violation reporting with photo evidence
- Notice generation and tracking
- Hearing scheduling
- Fine assessment and tracking
- Compliance verification
- Historical violation tracking per property

## Technical Design

### Violation Workflow
1. Report violation (with photos)
2. Send notice to owner
3. Owner has X days to cure
4. If not cured → Hearing scheduled
5. Hearing outcome → Fine or compliance
6. Track until resolved

### Models
- **Violation**: Core violation with status tracking
- **ViolationPhoto**: Photo evidence storage
- **ViolationNotice**: Notice history
- **ViolationHearing**: Hearing scheduling and outcomes

---
