# Sprint 15 - Advanced Reporting System

**Sprint Duration:** 2025-10-28
**Sprint Goal:** Build custom report builder for ad-hoc financial reporting
**Status:** Active

## Sprint Goal

Enable users to create custom financial reports without developer involvement. Users can:
- Define report templates with custom columns and filters
- Save and reuse reports
- Export to CSV/Excel/PDF
- Schedule automated report delivery (future)

## Scope

### High Priority
- CustomReport model (name, description, report_type, columns, filters)
- Report execution engine
- CSV export functionality
- Basic UI for report listing

### Medium Priority
- Excel export
- Report scheduling
- Email delivery

### Low Priority
- PDF export with charts
- Report sharing between users

## Technical Design

### Models
- **CustomReport**: Saved report definitions
- **ReportExecution**: Execution history and cached results

### Report Types
- General Ledger
- Trial Balance
- Income Statement
- Balance Sheet
- Cash Flow
- AR Aging (custom filters)
- Owner Ledger (custom filters)

---
