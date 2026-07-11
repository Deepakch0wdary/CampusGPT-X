import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, CircularProgress,
  Button, List, ListItem, ListItemText, Divider, Chip, Alert
} from '@mui/material';
import {
  Payment as PayIcon, Receipt as ReceiptIcon,
  Timeline, ErrorOutline
} from '@mui/icons-material';

import { useNavigate } from 'react-router-dom';

const api = async (path: string, method = 'GET', body?: any) => {
  const token = localStorage.getItem('access_token');
  const res = await fetch(`/api/v1/finance${path}`, {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  return res.json();
};

export const StudentFinanceDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [holds, setHolds] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDetails = async () => {
    try {
      const uStr = localStorage.getItem('user');
      if (!uStr) return;
      const user = JSON.parse(uStr);

      const [sumRes, invRes, holdRes] = await Promise.all([
        fetch(`/api/v1/finance/parent/children/${user.id}/summary`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        }).then(r => r.json()),
        api('/invoices/me'),
        api('/holds/me')
      ]);

      if (sumRes.success) setSummary(sumRes.data);
      if (invRes.success) setInvoices(invRes.data);
      if (holdRes.success) setHolds(holdRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, []);

  if (loading) {
    return (
      <Box p={4} display="flex" justifyContent="center">
        <CircularProgress />
      </Box>
    );
  }

  const s = summary || { totalBilled: 0, totalPaid: 0, outstandingBalance: 0, overdueAmount: 0 };

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }} color="primary">
        Candidate Financial Dashboard
      </Typography>

      {s.hasFinancialHold && (
        <Alert severity="error" sx={{ mb: 3 }} icon={<ErrorOutline />}>
          Your portal access is currently restricted due to an active Financial Hold. Please clear outstanding dues immediately.
        </Alert>
      )}

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={3}>
          <Card sx={{ bgcolor: 'background.paper', borderRadius: 3, borderLeft: '6px solid #0070f3' }}>
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">Total Billed</Typography>
              <Typography variant="h4" fontWeight="bold">{s.totalBilled} INR</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card sx={{ bgcolor: 'background.paper', borderRadius: 3, borderLeft: '6px solid #4caf50' }}>
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">Total Paid</Typography>
              <Typography variant="h4" fontWeight="bold">{s.totalPaid} INR</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card sx={{ bgcolor: 'background.paper', borderRadius: 3, borderLeft: '6px solid #f44336' }}>
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">Outstanding Balance</Typography>
              <Typography variant="h4" fontWeight="bold" color="error">{s.outstandingBalance} INR</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card sx={{ bgcolor: 'background.paper', borderRadius: 3, borderLeft: '6px solid #ff9800' }}>
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">Overdue Dues</Typography>
              <Typography variant="h4" fontWeight="bold" color="warning.main">{s.overdueAmount} INR</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Invoices List */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Recent Invoices</Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              {invoices.length === 0 ? (
                <Typography color="textSecondary">No fee invoices issued yet.</Typography>
              ) : (
                invoices.map((inv) => (
                  <ListItem key={inv.id} divider sx={{ py: 2 }}>
                    <ListItemText
                      primary={`Invoice: ${inv.invoiceNumber}`}
                      secondary={`Due: ${inv.dueDate ? inv.dueDate.split('T')[0] : 'N/A'}`}
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Chip label={inv.status} color={inv.status === 'PAID' ? 'success' : 'warning'} size="small" />
                      <Typography fontWeight="bold">{inv.balanceAmount} INR Outstanding</Typography>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => navigate(`/invoice/${inv.id}`)}
                      >
                        Details
                      </Button>
                    </Box>
                  </ListItem>
                ))
              )}
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, borderRadius: 3, mb: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Active Holds</Typography>
            <Divider sx={{ mb: 2 }} />
            {holds.length === 0 ? (
              <Typography color="textSecondary">No active financial holds. Good standing.</Typography>
            ) : (
              holds.map(h => (
                <Box key={h.id} sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="error" fontWeight="bold">{h.reason}</Typography>
                  <Typography variant="caption" color="textSecondary">Placed on: {h.placedAt.split('T')[0]}</Typography>
                </Box>
              ))
            )}
          </Paper>

          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Quick Actions</Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Button fullWidth variant="contained" startIcon={<PayIcon />} onClick={() => navigate('/my-payments')}>
                  Payments
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Button fullWidth variant="outlined" startIcon={<ReceiptIcon />} onClick={() => navigate('/my-receipts')}>
                  Receipts
                </Button>
              </Grid>
              <Grid item xs={12}>
                <Button fullWidth variant="outlined" startIcon={<Timeline />} onClick={() => navigate('/ledger')}>
                  Ledger History
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
