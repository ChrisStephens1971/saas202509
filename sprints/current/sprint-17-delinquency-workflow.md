# Sprint 17 - Delinquency Workflow & Collections

**Sprint Duration:** 2025-10-29
**Sprint Goal:** Automate collections workflow with late fees and notice tracking
**Status:** Active

## Sprint Goal

Build automated delinquency management system that:
- Auto-calculates late fees based on configurable rules
- Tracks owner delinquency status (current, 30/60/90+ days)
- Manages collection notices (email, certified mail)
- Provides board approval workflow for liens
- State-specific lien rules (CA, FL, TX)

## Technical Design

### Models
- **LateFeeRule**: Configurable late fee calculation
- **DelinquencyStatus**: Per-owner delinquency tracking
- **CollectionNotice**: Notice history with delivery confirmation
- **CollectionAction**: Attorney referrals, liens, foreclosures

### Workflow
Day 0: Invoice issued
Day 10: Payment due
Day 20: Grace period ends → Auto late fee
Day 35: Second notice (email + certified mail)
Day 60: Final notice → Flag as lien eligible
Day 90: Attorney escalation workflow

---
