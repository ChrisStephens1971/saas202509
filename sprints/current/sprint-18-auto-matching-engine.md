# Sprint 18 - Auto-Matching Engine

**Sprint Duration:** 2025-10-29
**Sprint Goal:** Achieve 90%+ auto-match rate for bank transactions
**Status:** Active

## Sprint Goal

Enhance bank reconciliation with intelligent auto-matching that learns from past matches:
- Multi-rule matching (exact, fuzzy, pattern, ML)
- Confidence scoring
- Match suggestions with explanations
- Pattern learning from historical matches
- 90-95% auto-match target

## Technical Design

### Matching Rules (Priority Order)
1. **Exact Match** (100% confidence): Amount + Date ±0 days
2. **Fuzzy Match** (95% confidence): Amount ±$1 + Date ±3 days
3. **Reference Match** (90% confidence): Check#, Invoice#, Stripe ID
4. **Pattern Match** (85% confidence): Description patterns
5. **ML Match** (variable): Learn from historical matches

### Models
- **AutoMatchRule**: Learned matching patterns
- **MatchResult**: Cached match results with confidence
- **MatchStatistics**: Track match rates and accuracy

---
