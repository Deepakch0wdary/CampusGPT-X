import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, CircularProgress,
  List, ListItem, ListItemText, Divider, Chip, FormControl,
  InputLabel, Select, MenuItem, Alert
} from '@mui/material';
import { ErrorOutline } from '@mui/icons-material';

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

export const ParentFinanceDashboard: React.FC = () => {
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChild, setSelectedChild] = useState<string>('');
  const [summary, setSummary] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchChildren = async () => {
    try {
      const res = await api('/parent/children');
      if (res.success && res.data.length > 0) {
        setChildren(res.data);
        setSelectedChild(res.data[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchChildDetails = async (childId: string) => {
    if (!childId) return;
    try {
      const [sumRes, invRes] = await Promise.all([
        api(`/parent/children/${childId}/summary`),
        api(`/parent/children/${childId}/invoices`)
      ]);
      if (sumRes.success) setSummary(sumRes.data);
      if (invRes.success) setInvoices(invRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchChildren();
  }, []);

  useEffect(() => {
    if (selectedChild) {
      fetchChildDetails(selectedChild);
    }
  }, [selectedChild]);

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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold" color="primary">
          Parent Finance Dashboard
        </Typography>

        {children.length > 0 && (
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Select Child</InputLabel>
            <Select
              value={selectedChild}
              onChange={(e) => setSelectedChild(e.target.value)}
              label="Select Child"
            >
              {children.map(c => (
                <MenuItem key={c.id} value={c.id}>{c.name} ({c.relationship})</MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </Box>

      {children.length === 0 ? (
        <Alert severity="warning">No children linked to your parent profile.</Alert>
      ) : (
        <>
          {s.hasFinancialHold && (
            <Alert severity="error" sx={{ mb: 3 }} icon={<ErrorOutline />}>
              Active Financial Hold exists on child's account. Educational portals and libraries are locked.
            </Alert>
          )}

          {/* Metrics */}
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
                  <Typography color="textSecondary" variant="subtitle2">Overdue Amount</Typography>
                  <Typography variant="h4" fontWeight="bold" color="warning.main">{s.overdueAmount} INR</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Child's Invoices */}
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Child's Invoice Registry</Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              {invoices.length === 0 ? (
                <Typography color="textSecondary">No fee invoices issued.</Typography>
              ) : (
                invoices.map((inv) => (
                  <ListItem key={inv.id} divider sx={{ py: 2 }}>
                    <ListItemText
                      primary={`Invoice: ${inv.invoiceNumber}`}
                      secondary={`Due: ${inv.dueDate ? inv.dueDate.split('T')[0] : 'N/A'}`}
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Chip label={inv.status} color={inv.status === 'PAID' ? 'success' : 'warning'} size="small" />
                      <Typography fontWeight="bold">{inv.balanceAmount} INR</Typography>
                    </Box>
                  </ListItem>
                ))
              )}
            </List>
          </Paper>
        </>
      )}
    </Box>
  );
};
