# Sprint 20 - Board Packet Generation

**Sprint Duration:** 2025-10-29
**Sprint Goal:** One-click PDF board packet generation
**Status:** Active

## Sprint Goal

Enable treasurers to generate comprehensive board packets in one click:
- Customizable packet templates
- Include financial reports (trial balance, cash flow, etc.)
- Include agendas and minutes
- Include AR aging and delinquency reports
- PDF generation and archiving
- Email distribution to board members

## Technical Design

### Packet Components
1. Cover page
2. Meeting agenda
3. Financial reports (selectable)
4. AR aging report
5. Delinquency status
6. Violation summary
7. Reserve study summary (optional)
8. Attachments (documents, photos)

### Models
- **BoardPacketTemplate**: Reusable packet templates
- **BoardPacket**: Generated packets with PDF
- **PacketSection**: Configurable sections

---
