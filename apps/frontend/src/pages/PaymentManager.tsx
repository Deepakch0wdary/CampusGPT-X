import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, TextField, Button, Table, TableHead,
  TableRow, TableCell, TableBody, MenuItem, FormControl, InputLabel,
  Select, Alert, Grid
} from '@mui/material';

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

export const PaymentManager: React.FC = () => {
  const [payments, setPayments] = useState<any[]>([]);
  const [invoiceId, setInvoiceId] = useState('');
  const [amount, setAmount] = useState(10000);
  const [method, setMethod] = useState('UPI');
  const [message, setMessage] = useState<string | null>(null);

  const fetchPayments = async () => {
    const res = await fetch('/api/v1/payments', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json());
    if (res.success) setPayments(res.data);
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  const handleSimulate = async () => {
    const res = await api('/payments/demo', 'POST', {
      invoiceId,
      amount,
      method,
      idempotencyKey: `pay-mgr-${Date.now()}`
    });
    if (res.success) {
      setMessage(`Demo payment registered successfully! Reference: ${res.data.paymentNumber}`);
      fetchPayments();
    } else {
      setMessage(`Error: ${res.detail || 'Failed to process payment'}`);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 2 }}>Payment Recording Desk</Typography>

      <Alert severity="warning" sx={{ mb: 3, fontWeight: 'bold' }}>
        DEMO PAYMENT — NO REAL MONEY MOVED
      </Alert>

      {message && (
        <Alert severity="info" sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          {message}
        </Alert>
      )}

      <Paper sx={{ p: 3, borderRadius: 3, mb: 4 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Record Simulated Payment</Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <TextField label="Invoice ID" fullWidth value={invoiceId} onChange={e => setInvoiceId(e.target.value)} />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField label="Amount" type="number" fullWidth value={amount} onChange={e => setAmount(Number(e.target.value))} />
          </Grid>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth>
              <InputLabel>Method</InputLabel>
              <Select value={method} onChange={e => setMethod(e.target.value)} label="Method">
                <MenuItem value="CASH">Cash</MenuItem>
                <MenuItem value="UPI">UPI Transfer</MenuItem>
                <MenuItem value="CREDIT_CARD">Credit Card</MenuItem>
                <MenuItem value="DEBIT_CARD">Debit Card</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button fullWidth variant="contained" color="success" onClick={handleSimulate}>
              Submit Simulated Payment
            </Button>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Payment Transaction History</Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Payment ID</TableCell>
              <TableCell>Collected Amount</TableCell>
              <TableCell>Method</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {payments.map(p => (
              <TableRow key={p.id}>
                <TableCell sx={{ fontWeight: 'bold' }}>{p.paymentNumber}</TableCell>
                <TableCell>{p.amount} INR</TableCell>
                <TableCell>{p.method}</TableCell>
                <TableCell>{p.status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};
export default PaymentManager;
