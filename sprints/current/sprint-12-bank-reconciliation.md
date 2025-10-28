# Sprint 12 - Bank Reconciliation & Transaction Matching

**Sprint Duration:** 2025-10-28 (1-2 day sprint)
**Sprint Goal:** Build manual bank reconciliation UI with transaction matching capabilities
**Status:** 🏗️ In Progress

---

## Sprint Goal

Implement a comprehensive bank reconciliation interface that allows users to:
1. Import bank statements (CSV/OFX)
2. Match imported transactions to existing journal entries
3. Create new journal entries for unmatched transactions
4. Mark transactions as reconciled
5. Generate reconciliation reports with beginning/ending balances

**Success Criteria:**
- Users can upload bank statements and see imported transactions
- System suggests matches based on amount, date, and description
- Users can manually match transactions or create new entries
- Reconciliation status tracked (matched, unmatched, ignored)
- Reconciliation report shows cleared vs uncleared items
- All operations maintain double-entry bookkeeping integrity

---

## Sprint Backlog

### High Priority (Must Complete)

| Story | Description | Estimate | Status | Notes |
|-------|-------------|----------|--------|-------|
| HOA-1201 | Backend reconciliation API endpoints | L | 📋 Todo | CRUD for bank statements |
| HOA-1202 | Transaction import parser (CSV/OFX) | M | 📋 Todo | Parse bank statement formats |
| HOA-1203 | Matching algorithm implementation | L | 📋 Todo | Fuzzy matching logic |
| HOA-1204 | Reconciliation UI layout | M | 📋 Todo | Split-pane interface |
| HOA-1205 | Transaction matching interface | L | 📋 Todo | Drag-and-drop or click to match |
| HOA-1206 | Create journal entry from transaction | M | 📋 Todo | Quick-create modal |

### Medium Priority (Should Complete)

| Story | Description | Estimate | Status | Notes |
|-------|-------------|----------|--------|-------|
| HOA-1207 | Auto-match suggestions | M | 📋 Todo | ML-based matching |
| HOA-1208 | Reconciliation report | M | 📋 Todo | Beginning/ending balance |
| HOA-1209 | Bulk actions (match/ignore) | S | 📋 Todo | Multi-select operations |
| HOA-1210 | Transaction notes and tagging | S | 📋 Todo | Add context to transactions |

### Low Priority (Nice to Have)

| Story | Description | Estimate | Status | Notes |
|-------|-------------|----------|--------|-------|
| HOA-1211 | Rule-based auto-matching | M | 📋 Todo | Save matching rules |
| HOA-1212 | Bank account connection (Plaid) | XL | 📋 Todo | Future: automatic import |
| HOA-1213 | Multi-currency support | L | 📋 Todo | Future: international |

---

## Backend Implementation

### Models to Create/Extend

**File:** `backend/accounting/models.py`

```python
class BankStatement(models.Model):
    """Imported bank statement"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    statement_date = models.DateField()
    beginning_balance = models.DecimalField(max_digits=15, decimal_places=2)
    ending_balance = models.DecimalField(max_digits=15, decimal_places=2)
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    reconciled = models.BooleanField(default=False)
    reconciled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-statement_date']


class BankTransaction(models.Model):
    """Individual transaction from bank statement"""
    STATUS_CHOICES = [
        ('unmatched', 'Unmatched'),
        ('matched', 'Matched'),
        ('ignored', 'Ignored'),
        ('created', 'Journal Entry Created'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateField()
    post_date = models.DateField(null=True, blank=True)
    description = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)  # Positive = deposit, Negative = withdrawal
    check_number = models.CharField(max_length=50, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)

    # Matching
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unmatched')
    matched_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    match_confidence = models.IntegerField(default=0)  # 0-100 score
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['transaction_date', '-amount']


class ReconciliationRule(models.Model):
    """Saved rules for automatic matching"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description_pattern = models.CharField(max_length=255)  # Regex or contains
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    amount_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
```

### API Endpoints

**File:** `backend/accounting/api_views.py`

```python
class BankReconciliationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def upload_statement(self, request):
        """Upload and parse bank statement (CSV/OFX)"""
        # Parse file, create BankStatement and BankTransaction records
        pass

    @action(detail=False, methods=['get'])
    def statements(self, request):
        """List all bank statements"""
        pass

    @action(detail=True, methods=['get'])
    def statement_detail(self, request, pk=None):
        """Get statement with all transactions"""
        pass

    @action(detail=False, methods=['get'])
    def unmatched_transactions(self, request):
        """Get all unmatched bank transactions"""
        pass

    @action(detail=False, methods=['post'])
    def suggest_matches(self, request):
        """Suggest matches for a bank transaction"""
        # Fuzzy matching algorithm
        # - Exact amount match
        # - Date proximity (±3 days)
        # - Description similarity (Levenshtein distance)
        # - Check number match
        pass

    @action(detail=False, methods=['post'])
    def match_transaction(self, request):
        """Match a bank transaction to a journal entry"""
        pass

    @action(detail=False, methods=['post'])
    def unmatch_transaction(self, request):
        """Unmatch a previously matched transaction"""
        pass

    @action(detail=False, methods=['post'])
    def ignore_transaction(self, request):
        """Mark transaction as ignored"""
        pass

    @action(detail=False, methods=['post'])
    def create_from_transaction(self, request):
        """Create journal entry from bank transaction"""
        pass

    @action(detail=True, methods=['get'])
    def reconciliation_report(self, request, pk=None):
        """Generate reconciliation report for a statement"""
        # Beginning balance
        # + Deposits (matched)
        # - Withdrawals (matched)
        # = Ending balance
        # Unmatched items
        pass
```

---

## Frontend Implementation

### Component Structure

```
frontend/src/components/reconciliation/
├── BankStatementUpload.tsx       - Upload CSV/OFX files
├── StatementList.tsx              - List of uploaded statements
├── ReconciliationWorkspace.tsx    - Main split-pane interface
├── BankTransactionList.tsx        - Left pane: bank transactions
├── JournalEntryList.tsx           - Right pane: journal entries
├── TransactionMatchCard.tsx       - Individual transaction card
├── MatchSuggestions.tsx           - Suggested matches popup
├── CreateEntryModal.tsx           - Quick-create journal entry
├── ReconciliationReport.tsx       - Final reconciliation report
└── ReconciliationSummary.tsx      - Summary stats (matched/unmatched)
```

### Pages

```
frontend/src/pages/
├── BankReconciliationPage.tsx     - Main reconciliation page
└── ReconciliationHistoryPage.tsx  - Past reconciliations
```

### API Client

**File:** `frontend/src/api/reconciliation.ts`

```typescript
export interface BankStatement {
  id: string
  fund: string | Fund
  statement_date: string
  beginning_balance: string
  ending_balance: string
  file_name: string
  uploaded_at: string
  reconciled: boolean
  reconciled_at: string | null
}

export interface BankTransaction {
  id: string
  statement: string
  transaction_date: string
  description: string
  amount: string
  check_number: string
  reference_number: string
  status: 'unmatched' | 'matched' | 'ignored' | 'created'
  matched_entry: string | null
  match_confidence: number
  notes: string
}

export interface MatchSuggestion {
  journal_entry: JournalEntry
  confidence: number
  reason: string
}

export interface ReconciliationReport {
  statement: BankStatement
  beginning_balance: string
  deposits: string
  withdrawals: string
  ending_balance: string
  calculated_balance: string
  difference: string
  matched_count: number
  unmatched_count: number
  transactions: BankTransaction[]
}

export const reconciliationApi = {
  uploadStatement: async (file: File, fundId: string, statementDate: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('fund', fundId)
    formData.append('statement_date', statementDate)

    const response = await client.post('/api/v1/accounting/reconciliation/upload-statement/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  getStatements: async (params?: { fund?: string, reconciled?: boolean }) => {
    const response = await client.get('/api/v1/accounting/reconciliation/statements/', { params })
    return response.data
  },

  getStatementDetail: async (id: string): Promise<BankStatement> => {
    const response = await client.get(`/api/v1/accounting/reconciliation/statement-detail/${id}/`)
    return response.data
  },

  getUnmatchedTransactions: async (statementId?: string) => {
    const response = await client.get('/api/v1/accounting/reconciliation/unmatched-transactions/', {
      params: { statement: statementId }
    })
    return response.data
  },

  suggestMatches: async (transactionId: string): Promise<MatchSuggestion[]> => {
    const response = await client.post('/api/v1/accounting/reconciliation/suggest-matches/', {
      transaction_id: transactionId
    })
    return response.data
  },

  matchTransaction: async (transactionId: string, entryId: string) => {
    const response = await client.post('/api/v1/accounting/reconciliation/match-transaction/', {
      transaction_id: transactionId,
      entry_id: entryId
    })
    return response.data
  },

  unmatchTransaction: async (transactionId: string) => {
    const response = await client.post('/api/v1/accounting/reconciliation/unmatch-transaction/', {
      transaction_id: transactionId
    })
    return response.data
  },

  ignoreTransaction: async (transactionId: string, notes: string) => {
    const response = await client.post('/api/v1/accounting/reconciliation/ignore-transaction/', {
      transaction_id: transactionId,
      notes
    })
    return response.data
  },

  createFromTransaction: async (transactionId: string, data: {
    account: string
    fund: string
    description: string
  }) => {
    const response = await client.post('/api/v1/accounting/reconciliation/create-from-transaction/', {
      transaction_id: transactionId,
      ...data
    })
    return response.data
  },

  getReconciliationReport: async (statementId: string): Promise<ReconciliationReport> => {
    const response = await client.get(`/api/v1/accounting/reconciliation/reconciliation-report/${statementId}/`)
    return response.data
  }
}
```

---

## UI Design

### Reconciliation Workspace Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Bank Reconciliation - Operating Fund - October 2025             │
│ [Upload Statement] [Settings] [View Reports]                    │
├─────────────────────────────────────────────────────────────────┤
│ Statement: Oct 2025 | Beginning: $85,500 | Ending: $92,300     │
│ Matched: 45 | Unmatched: 8 | Difference: $0.00 ✓              │
├──────────────────────────────┬──────────────────────────────────┤
│ Bank Transactions (8)        │ Journal Entries (Search)         │
│ [Filter] [Sort] [Bulk]       │ [Date Range] [Account]           │
├──────────────────────────────┼──────────────────────────────────┤
│ ☐ 10/15 Dues Payment         │ ⚪ 10/15 Invoice #1025 Payment   │
│    HOA DUES - UNIT 15B       │    Unit 15B - $325.00            │
│    $325.00                   │    Operating Fund                │
│    [Match] [Ignore] [Create] │    [Match This]                  │
│    📊 98% match confidence   │                                  │
├──────────────────────────────┼──────────────────────────────────┤
│ ☐ 10/18 Vendor Payment       │ ⚪ 10/18 Pool Service Expense    │
│    CLEAR WATER POOLS         │    Pool Maintenance              │
│    -$450.00                  │    -$450.00                      │
│    [Match] [Ignore] [Create] │    [Match This]                  │
│    📊 95% match confidence   │                                  │
├──────────────────────────────┼──────────────────────────────────┤
│ ☐ 10/22 Transfer             │ No matches found                 │
│    TRANSFER FROM RESERVE     │                                  │
│    $5,000.00                 │                                  │
│    [Match] [Ignore] [Create] │    [Create Entry]                │
│    📊 No match found         │                                  │
└──────────────────────────────┴──────────────────────────────────┘
```

### Features:
- **Split-pane interface** - Bank transactions on left, journal entries on right
- **Drag-and-drop** - Drag bank transaction onto journal entry to match
- **Click to match** - Click both items and click "Match" button
- **Auto-suggestions** - System highlights likely matches with confidence score
- **Quick actions** - Match, Ignore, or Create Entry from each transaction
- **Real-time updates** - Summary stats update as transactions are matched
- **Bulk operations** - Select multiple transactions for bulk actions

---

## Matching Algorithm

### Fuzzy Matching Logic

**Priority 1: Exact Match (100% confidence)**
- Amount matches exactly
- Date within ±1 day
- Description contains key terms

**Priority 2: High Confidence (80-99%)**
- Amount matches exactly
- Date within ±3 days
- Description similarity > 70% (Levenshtein)

**Priority 3: Medium Confidence (50-79%)**
- Amount matches exactly
- Date within ±7 days
- Any description similarity

**Priority 4: Low Confidence (< 50%)**
- Amount within ±$5
- Date within ±14 days
- Description contains related terms

### Matching Factors:
1. **Amount** - Primary matching criteria
2. **Date proximity** - Closer dates = higher confidence
3. **Description similarity** - Levenshtein distance algorithm
4. **Check number** - If present, must match exactly
5. **Historical patterns** - Learn from user's previous matches

---

## File Parsing

### Supported Formats

**CSV Format:**
```csv
Date,Description,Amount,Check Number,Balance
10/15/2024,"HOA DUES - UNIT 15B",325.00,,45325.00
10/18/2024,"CLEAR WATER POOLS",-450.00,1234,44875.00
```

**OFX Format (Simple):**
```xml
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20241015</DTPOSTED>
            <TRNAMT>325.00</TRNAMT>
            <NAME>HOA DUES - UNIT 15B</NAME>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
```

---

## Testing Plan

### Backend Tests
1. **BankStatement model** - CRUD operations
2. **CSV parser** - Various CSV formats
3. **OFX parser** - Standard OFX files
4. **Matching algorithm** - Test all confidence levels
5. **Reconciliation report** - Balance calculations

### Frontend Tests
1. **File upload** - CSV/OFX file handling
2. **Transaction list** - Filtering and sorting
3. **Matching interface** - Drag-and-drop functionality
4. **Create entry modal** - Form validation
5. **Report generation** - Data display

### Manual Testing
- [ ] Upload bank statement (CSV)
- [ ] Upload bank statement (OFX)
- [ ] View unmatched transactions
- [ ] Match transaction manually
- [ ] Accept suggested match
- [ ] Ignore transaction
- [ ] Create journal entry from transaction
- [ ] Generate reconciliation report
- [ ] Verify beginning/ending balance calculations
- [ ] Test bulk operations

---

## Performance Considerations

- Index `BankTransaction.status` for filtering
- Index `BankTransaction.transaction_date` for sorting
- Cache matching suggestions (5 minutes)
- Lazy load transaction lists (pagination)
- Debounce search/filter inputs
- Background processing for large imports (Celery)

---

## Dependencies

### Backend
- **ofxparse** - OFX file parsing (new)
- **python-Levenshtein** - String similarity (new)
- Existing: Django, DRF, PostgreSQL

### Frontend
- **react-dropzone** - File upload (new)
- **react-beautiful-dnd** - Drag and drop (new, optional)
- Existing: React, TypeScript, Tailwind, React Hook Form

---

## Sprint Metrics

**Estimated Effort:**
- Backend: 4-5 hours (models, API, parsing, matching)
- Frontend: 5-6 hours (UI, components, API integration)
- Testing: 2-3 hours
- **Total: 1-2 day sprint**

**Deliverables:**
- 3 new models (BankStatement, BankTransaction, ReconciliationRule)
- 8-10 API endpoints
- 2 new pages
- 9 new components
- CSV/OFX parsers
- Matching algorithm

---

## Next Steps (Sprint 13)

Potential priorities after bank reconciliation:
1. **Reserve Planning Module** - 5-20 year forecasting
2. **Advanced Reporting** - Custom report builder
3. **Email Notification Preferences** - User settings UI
4. **Audit Trail** - Complete transaction history with changes
5. **Vendor Management** - Vendor portal and bill pay

---

## Links & References

- **Related Sprints:**
  - Sprint 9: Automation and Banking (payment import backend)
  - Sprint 11: Dashboard (financial metrics display)

- **Documentation:**
  - Bank Reconciliation: [Accounting standards]
  - OFX Format: https://financialdataexchange.org/FDX/About/OFX-Work-Group.aspx
  - CSV Parsing: Python csv module

---

**Sprint 12 Status:** 🏗️ In Progress
**Started:** 2025-10-28
**Target Completion:** 2025-10-29 (1-2 days)
