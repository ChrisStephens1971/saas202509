# Sprint 21 - Auditor Export

**Sprint Duration:** 2025-10-31 to 2025-11-07 (1 week)
**Sprint Goal:** Enable audit-grade financial data exports
**Status:** Planned
**Phase:** Phase 4 - Retention Features

## Sprint Goal

Enable treasurers and management companies to export complete financial records for annual audits and external reviews:
- Full general ledger export with all journal entries
- CSV format compatible with auditor software (QuickBooks, Xero, etc.)
- Immutable, timestamped exports (audit trail)
- Evidence linking (supporting documents, receipts, photos)
- Date range selection and filtering
- Multiple export formats (CSV, Excel, PDF report)

## User Stories

### US-21.1: Generate Audit Export
**As a** HOA treasurer
**I want to** export a complete general ledger for a date range
**So that** I can provide auditors with all financial records they need

**Acceptance Criteria:**
- Select start and end dates for export
- Export includes all journal entries, transactions, and balances
- CSV format with standard accounting columns
- Export is immutable once generated
- Timestamp recorded for audit trail
- Download link provided immediately

**Estimated Effort:** 3 days

---

### US-21.2: Link Evidence to Transactions
**As an** auditor
**I want to** access supporting documents for transactions
**So that** I can verify expenses and validate financial records

**Acceptance Criteria:**
- Each transaction row includes evidence URLs
- Evidence types: receipts, invoices, photos, work orders, ARC documents
- Links are secure and time-limited
- Missing evidence is clearly marked
- Evidence is organized by transaction ID

**Estimated Effort:** 2 days

---

### US-21.3: Export Management Dashboard
**As a** treasurer
**I want to** view and manage all generated audit exports
**So that** I can track what was sent to auditors and when

**Acceptance Criteria:**
- List all generated exports with metadata
- Show: date range, generated date, file size, download count
- Re-download previous exports
- Delete old exports (with confirmation)
- Search and filter by date

**Estimated Effort:** 2 days

---

## Technical Design

### Overview

Auditor export follows a similar pattern to Sprint 20 (Board Packets):
1. User specifies date range and export options
2. System generates immutable export file (CSV/Excel)
3. Export is stored with metadata and timestamp
4. User downloads export or shares with auditor

### Data Model

```python
class AuditorExport(models.Model):
    """
    Immutable audit export with timestamp and metadata.
    Once generated, cannot be modified (audit trail).
    """
    tenant = models.ForeignKey(Tenant)
    title = models.CharField(max_length=200)  # e.g., "2025 Annual Audit Export"
    start_date = models.DateField()  # Beginning of date range
    end_date = models.DateField()    # End of date range

    # Export options
    format = models.CharField(choices=['csv', 'excel', 'pdf'])
    include_evidence = models.BooleanField(default=True)
    include_balances = models.BooleanField(default=True)
    include_owner_data = models.BooleanField(default=False)  # Privacy flag

    # File storage
    file_url = models.URLField(blank=True)  # S3 or local storage
    file_size_bytes = models.IntegerField(default=0)
    file_hash = models.CharField(max_length=64)  # SHA-256 for integrity

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User)
    status = models.CharField(
        choices=['generating', 'ready', 'failed'],
        default='generating'
    )

    # Audit trail
    downloaded_count = models.IntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True)

    # Summary stats
    total_entries = models.IntegerField(default=0)
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    evidence_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"
```

### CSV Export Schema

**Standard Auditor CSV Format:**

```csv
Date,Entry#,Account#,Account Name,Description,Debit,Credit,Balance,Evidence URL,Notes
2025-01-15,JE-001,1000,Cash,Monthly assessment revenue,,5000.00,5000.00,https://...,Payment batch #123
2025-01-15,JE-001,4000,HOA Dues Revenue,Monthly assessment revenue,5000.00,,0.00,,Unit 101-150
2025-02-20,JE-045,5100,Landscaping Expense,February landscape invoice,1200.00,,1200.00,https://.../invoice.pdf,Vendor: GreenScape
```

**Required Columns:**
- `Date`: Transaction date (YYYY-MM-DD)
- `Entry#`: Journal entry number
- `Account#`: Chart of accounts code
- `Account Name`: Account description
- `Description`: Transaction description
- `Debit`: Debit amount (or blank)
- `Credit`: Credit amount (or blank)
- `Balance`: Running balance for account
- `Evidence URL`: Link to supporting documents
- `Notes`: Additional context

### API Endpoints

```python
# ViewSet: AuditorExportViewSet

POST   /api/v1/accounting/auditor-exports/
    Create new export request
    Body: {
        "title": "2025 Annual Audit",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "format": "csv",
        "include_evidence": true
    }

GET    /api/v1/accounting/auditor-exports/
    List all exports for tenant

GET    /api/v1/accounting/auditor-exports/:id/
    Get export details

POST   /api/v1/accounting/auditor-exports/:id/generate/
    Generate export file (async)
    Returns: {"status": "generating", "export_id": 123}

GET    /api/v1/accounting/auditor-exports/:id/download/
    Download generated export file
    Increments download counter

DELETE /api/v1/accounting/auditor-exports/:id/
    Delete export (soft delete for audit trail)
```

### Export Generation Service

```python
# accounting/services/auditor_export_service.py

class AuditorExportService:
    """
    Generate audit-grade exports with evidence linking.
    """

    def generate_export(self, export_id):
        """
        Generate CSV/Excel export for auditor.

        Steps:
        1. Query all journal entries in date range
        2. Build CSV rows with running balances
        3. Attach evidence URLs for each entry
        4. Calculate totals and verify balance
        5. Generate file and upload to storage
        6. Update export record with metadata
        """

    def calculate_running_balance(self, account, entries):
        """Calculate running balance for account across entries"""

    def get_evidence_url(self, journal_entry):
        """
        Find supporting evidence for journal entry.
        Evidence sources:
        - Violation photos (Sprint 15)
        - Work order documents (Sprint 17)
        - ARC request documents (Sprint 16)
        - Bank statements (bank reconciliation)
        - Invoice uploads
        """

    def verify_export_integrity(self, export_data):
        """
        Verify export data integrity:
        - All debits = all credits (must balance)
        - No missing journal entries
        - All evidence links are valid
        - Date range is correct
        """
```

### Evidence Linking Strategy

**Evidence Sources (by transaction type):**

1. **Violation Fines** → Violation photos (Sprint 15)
2. **Work Orders** → Work order documents (Sprint 17)
3. **ARC Requests** → ARC documents (Sprint 16)
4. **Bank Deposits/Withdrawals** → Bank statements
5. **Vendor Payments** → Invoice uploads
6. **Owner Payments** → Payment receipts

**Evidence URL Format:**
```
https://app.hoaaccounting.com/evidence/{tenant_id}/{type}/{id}?token={jwt_token}
```

**Security:**
- Time-limited JWT tokens (valid for 7 days)
- Evidence URLs expire after export download
- Auditor access only (no owner access to other units' data)

### Frontend Components

**Pages:**
1. **AuditorExportsPage.tsx** - List and manage exports
2. **CreateExportModal.tsx** - Date range picker and options
3. **ExportDetailsPage.tsx** - View export metadata and download

**Key Features:**
- Date range picker (calendar UI)
- Export format selector (CSV, Excel, PDF)
- Progress indicator during generation
- Download button with file size
- Export history table

---

## Database Schema

**Migration:** `0015_add_auditor_export_model.py`

```sql
CREATE TABLE accounting_auditorexport (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES accounting_tenant(id),
    title VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    format VARCHAR(20) NOT NULL,
    include_evidence BOOLEAN DEFAULT TRUE,
    include_balances BOOLEAN DEFAULT TRUE,
    include_owner_data BOOLEAN DEFAULT FALSE,
    file_url VARCHAR(500),
    file_size_bytes INTEGER DEFAULT 0,
    file_hash VARCHAR(64),
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    generated_by_id INTEGER REFERENCES auth_user(id),
    status VARCHAR(20) DEFAULT 'generating',
    downloaded_count INTEGER DEFAULT 0,
    last_downloaded_at TIMESTAMPTZ,
    total_entries INTEGER DEFAULT 0,
    total_debit NUMERIC(15,2) DEFAULT 0,
    total_credit NUMERIC(15,2) DEFAULT 0,
    evidence_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT check_dates CHECK (end_date >= start_date),
    CONSTRAINT check_balance CHECK (total_debit = total_credit)
);

CREATE INDEX idx_auditorexport_tenant ON accounting_auditorexport(tenant_id);
CREATE INDEX idx_auditorexport_dates ON accounting_auditorexport(start_date, end_date);
```

---

## Testing Requirements

### Unit Tests
- CSV generation with correct formatting
- Running balance calculations
- Evidence URL generation
- Data integrity checks (debits = credits)

### Integration Tests
- Full export generation end-to-end
- Large dataset performance (10,000+ entries)
- Evidence linking across multiple sources
- Download tracking and audit trail

### Manual Testing
- Export opens correctly in Excel
- Auditor can follow evidence links
- Date range filtering is accurate
- File integrity (SHA-256 hash verification)

---

## Acceptance Criteria

Sprint 21 is complete when:
- ✅ Treasurers can generate audit exports for any date range
- ✅ CSV format is compatible with Excel and auditor tools
- ✅ Evidence URLs link to supporting documents
- ✅ Exports are immutable and timestamped
- ✅ Download tracking works correctly
- ✅ All debits equal all credits (verified)
- ✅ Frontend UI is intuitive and responsive
- ✅ Tests pass with 85%+ coverage
- ✅ Documentation is complete

---

## Dependencies

**Depends On:**
- Sprint 1-12: Core accounting models (Journal Entry, Account, etc.)
- Sprint 15: Violation tracking (evidence photos)
- Sprint 16: ARC workflow (documents)
- Sprint 17: Work order system (documents)
- Sprint 20: Board packet generation (file storage patterns)

**Required Libraries:**
- `openpyxl` or `xlsxwriter` for Excel export
- `csv` (Python standard library) for CSV export
- `hashlib` for file integrity (SHA-256)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large exports (100K+ entries) timeout | High | Implement async generation with progress tracking |
| Evidence links break after download | Medium | Use time-limited tokens with 7-day expiry |
| CSV format incompatible with auditor tools | High | Test with QuickBooks, Xero, and Excel |
| Missing evidence for old transactions | Low | Clearly mark missing evidence in export |
| Performance issues on large date ranges | Medium | Add pagination and streaming for large datasets |

---

## Next Steps After Sprint 21

**Sprint 22: Resale Disclosure Packages**
- Generate state-compliant disclosure documents
- Include financial statements, violations, liens
- Revenue opportunity ($200-500 per package)

**Sprint 23: Custom Report Builder**
- User-defined reports with drag-and-drop fields
- Save and share custom reports
- Scheduled report generation

---

## Success Metrics

- Export generation time: < 5 seconds for 1,000 entries
- CSV format compatibility: 100% (tested with Excel, QuickBooks, Xero)
- Evidence linking accuracy: > 95% of transactions have evidence
- User satisfaction: 4.5+ stars from treasurers
- Audit preparation time saved: 10+ hours per annual audit

---

**Sprint 21 Start Date:** TBD (pending approval)
**Estimated Effort:** 7 days (1 developer)
