/**
 * Resale Disclosures Page
 * Sprint 22 - Resale Disclosure Packages
 *
 * Generate state-compliant resale disclosure packages for unit sales.
 * Revenue opportunity: $200-500 per package
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Stack,
} from '@mui/material';
import {
  Add as AddIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  Receipt as ReceiptIcon,
  Refresh as RefreshIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';

import {
  ResaleDisclosure,
  CreateResaleDisclosureRequest,
  getResaleDisclosures,
  createResaleDisclosure,
  deleteResaleDisclosure,
  generateDisclosure,
  downloadDisclosure,
  deliverDisclosure,
  billDisclosure,
} from '../api/resaleDisclosures';

const ResaleDisclosuresPage: React.FC = () => {
  const [disclosures, setDisclosures] = useState<ResaleDisclosure[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Create disclosure modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateResaleDisclosureRequest>({
    unit: '',
    owner: '',
    buyer_name: '',
    escrow_agent: '',
    escrow_company: '',
    contact_email: '',
    contact_phone: '',
    state: 'CA',
    notes: '',
  });

  // Deliver disclosure modal
  const [deliverModalOpen, setDeliverModalOpen] = useState(false);
  const [selectedDisclosure, setSelectedDisclosure] = useState<ResaleDisclosure | null>(null);
  const [deliverEmails, setDeliverEmails] = useState<string>('');
  const [deliverMessage, setDeliverMessage] = useState<string>('');

  useEffect(() => {
    loadDisclosures();
  }, []);

  const loadDisclosures = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getResaleDisclosures();
      setDisclosures(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load resale disclosures');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDisclosure = async () => {
    try {
      setError(null);
      const newDisclosure = await createResaleDisclosure(createForm);
      setSuccess('Disclosure request created successfully!');
      setCreateModalOpen(false);

      // Auto-generate after creation
      await handleGenerateDisclosure(newDisclosure.id);

      loadDisclosures();

      // Reset form
      setCreateForm({
        unit: '',
        owner: '',
        buyer_name: '',
        escrow_agent: '',
        escrow_company: '',
        contact_email: '',
        contact_phone: '',
        state: 'CA',
        notes: '',
      });
    } catch (err: any) {
      setError(err.message || 'Failed to create disclosure request');
    }
  };

  const handleGenerateDisclosure = async (id: string) => {
    try {
      setError(null);
      setSuccess('Generating disclosure package...');
      await generateDisclosure(id);
      setSuccess('Disclosure package generated successfully!');
      loadDisclosures();
    } catch (err: any) {
      setError(err.message || 'Failed to generate disclosure package');
    }
  };

  const handleDownloadDisclosure = async (disclosure: ResaleDisclosure) => {
    try {
      setError(null);
      const filename = `resale_disclosure_${disclosure.unit_number}_${new Date(disclosure.requested_at).toISOString().split('T')[0]}.pdf`;
      await downloadDisclosure(disclosure.id, filename);
      setSuccess('Disclosure downloaded successfully!');
    } catch (err: any) {
      setError(err.message || 'Failed to download disclosure');
    }
  };

  const handleOpenDeliverModal = (disclosure: ResaleDisclosure) => {
    setSelectedDisclosure(disclosure);
    setDeliverEmails(disclosure.contact_email);
    setDeliverMessage('');
    setDeliverModalOpen(true);
  };

  const handleDeliverDisclosure = async () => {
    if (!selectedDisclosure) return;

    try {
      setError(null);
      const emailAddresses = deliverEmails.split(',').map(e => e.trim()).filter(e => e);
      await deliverDisclosure(selectedDisclosure.id, {
        email_addresses: emailAddresses,
        message: deliverMessage,
      });
      setSuccess(`Disclosure delivered to ${emailAddresses.length} recipient(s)!`);
      setDeliverModalOpen(false);
      loadDisclosures();
    } catch (err: any) {
      setError(err.message || 'Failed to deliver disclosure');
    }
  };

  const handleBillDisclosure = async (disclosure: ResaleDisclosure) => {
    try {
      setError(null);
      await billDisclosure(disclosure.id);
      setSuccess(`Invoice created for $${disclosure.fee_amount}!`);
      loadDisclosures();
    } catch (err: any) {
      setError(err.message || 'Failed to create invoice');
    }
  };

  const handleDeleteDisclosure = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this disclosure request?')) {
      return;
    }

    try {
      setError(null);
      await deleteResaleDisclosure(id);
      setSuccess('Disclosure deleted successfully!');
      loadDisclosures();
    } catch (err: any) {
      setError(err.message || 'Failed to delete disclosure');
    }
  };

  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'warning' => {
    switch (status) {
      case 'requested':
        return 'default';
      case 'generating':
        return 'primary';
      case 'ready':
        return 'success';
      case 'delivered':
        return 'secondary';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatDate = (dateString: string | undefined): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Resale Disclosure Packages
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Generate state-compliant disclosure packages for unit sales
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Tooltip title="Refresh">
            <IconButton onClick={loadDisclosures} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateModalOpen(true)}
          >
            New Disclosure Request
          </Button>
        </Stack>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Summary Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h3" color="primary">
              {disclosures.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Disclosures
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h3" color="success.main">
              {disclosures.filter(d => d.status === 'ready').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ready to Download
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h3" color="secondary.main">
              {disclosures.filter(d => d.status === 'delivered').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Delivered
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h3" color="text.primary">
              ${disclosures.reduce((sum, d) => sum + parseFloat(d.fee_amount || '0'), 0).toFixed(2)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Revenue
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Disclosures Grid */}
      <Grid container spacing={3}>
        {disclosures.map((disclosure) => (
          <Grid item xs={12} md={6} lg={4} key={disclosure.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Unit {disclosure.unit_number}
                    </Typography>
                    <Chip
                      label={disclosure.status_display}
                      color={getStatusColor(disclosure.status)}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <Chip
                      label={disclosure.state_display_name}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                  {disclosure.status === 'ready' && (
                    <DescriptionIcon color="success" fontSize="large" />
                  )}
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Buyer:</strong> {disclosure.buyer_name || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Escrow:</strong> {disclosure.escrow_company || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Contact:</strong> {disclosure.contact_email}
                </Typography>

                {disclosure.status === 'ready' && (
                  <Box sx={{ mt: 2, p: 1.5, bgcolor: 'success.light', borderRadius: 1 }}>
                    <Typography variant="caption" display="block" color="success.dark">
                      <strong>Pages:</strong> {disclosure.page_count} | <strong>Size:</strong> {formatFileSize(disclosure.pdf_size_bytes)}
                    </Typography>
                    {disclosure.has_violations && (
                      <Typography variant="caption" display="block" color="warning.dark">
                        <strong>Violations:</strong> {disclosure.violation_count} open
                      </Typography>
                    )}
                    {disclosure.has_lien && (
                      <Typography variant="caption" display="block" color="error.dark">
                        <strong>Lien:</strong> Active
                      </Typography>
                    )}
                  </Box>
                )}

                <Typography variant="caption" display="block" sx={{ mt: 2 }} color="text.secondary">
                  Requested: {formatDate(disclosure.requested_at)}
                </Typography>
                {disclosure.generated_at && (
                  <Typography variant="caption" display="block" color="text.secondary">
                    Generated: {formatDate(disclosure.generated_at)}
                  </Typography>
                )}
              </CardContent>

              <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                <Box>
                  {disclosure.status === 'requested' && (
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      onClick={() => handleGenerateDisclosure(disclosure.id)}
                    >
                      Generate
                    </Button>
                  )}
                  {disclosure.status === 'ready' && (
                    <>
                      <Tooltip title="Download PDF">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleDownloadDisclosure(disclosure)}
                        >
                          <DownloadIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Deliver to Buyer">
                        <IconButton
                          size="small"
                          color="secondary"
                          onClick={() => handleOpenDeliverModal(disclosure)}
                        >
                          <SendIcon />
                        </IconButton>
                      </Tooltip>
                      {!disclosure.invoice && (
                        <Tooltip title="Bill Owner ($${disclosure.fee_amount})">
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleBillDisclosure(disclosure)}
                          >
                            <ReceiptIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </>
                  )}
                </Box>
                <Tooltip title="Delete">
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDeleteDisclosure(disclosure.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {disclosures.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No disclosure requests yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first resale disclosure package to get started
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateModalOpen(true)}
          >
            New Disclosure Request
          </Button>
        </Paper>
      )}

      {/* Create Disclosure Modal */}
      <Dialog open={createModalOpen} onClose={() => setCreateModalOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>New Resale Disclosure Request</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Unit ID"
                  value={createForm.unit}
                  onChange={(e) => setCreateForm({ ...createForm, unit: e.target.value })}
                  required
                  helperText="Enter unit UUID"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Owner ID"
                  value={createForm.owner}
                  onChange={(e) => setCreateForm({ ...createForm, owner: e.target.value })}
                  required
                  helperText="Enter owner UUID"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Buyer Name"
                  value={createForm.buyer_name}
                  onChange={(e) => setCreateForm({ ...createForm, buyer_name: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Escrow Agent"
                  value={createForm.escrow_agent}
                  onChange={(e) => setCreateForm({ ...createForm, escrow_agent: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Escrow Company"
                  value={createForm.escrow_company}
                  onChange={(e) => setCreateForm({ ...createForm, escrow_company: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  select
                  label="State"
                  value={createForm.state}
                  onChange={(e) => setCreateForm({ ...createForm, state: e.target.value })}
                  required
                >
                  <MenuItem value="CA">California</MenuItem>
                  <MenuItem value="TX">Texas</MenuItem>
                  <MenuItem value="FL">Florida</MenuItem>
                  <MenuItem value="DEFAULT">Other</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="email"
                  label="Contact Email"
                  value={createForm.contact_email}
                  onChange={(e) => setCreateForm({ ...createForm, contact_email: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Contact Phone"
                  value={createForm.contact_phone}
                  onChange={(e) => setCreateForm({ ...createForm, contact_phone: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Notes"
                  value={createForm.notes}
                  onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateModalOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateDisclosure}
            variant="contained"
            disabled={!createForm.unit || !createForm.owner || !createForm.contact_email || !createForm.state}
          >
            Create & Generate
          </Button>
        </DialogActions>
      </Dialog>

      {/* Deliver Disclosure Modal */}
      <Dialog open={deliverModalOpen} onClose={() => setDeliverModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Deliver Disclosure Package</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Email Addresses"
              value={deliverEmails}
              onChange={(e) => setDeliverEmails(e.target.value)}
              helperText="Comma-separated email addresses"
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Message (Optional)"
              value={deliverMessage}
              onChange={(e) => setDeliverMessage(e.target.value)}
              helperText="Optional message to include in email"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeliverModalOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeliverDisclosure}
            variant="contained"
            startIcon={<SendIcon />}
            disabled={!deliverEmails}
          >
            Send
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ResaleDisclosuresPage;
