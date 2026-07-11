import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, TextField, Button, Table, TableHead, TableRow, TableCell, TableBody, Alert, Grid } from '@mui/material';

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

export const MyRefunds: React.FC = () => {
  const [refunds, setRefunds] = useState<any[]>([]);
  const [paymentId, setPaymentId] = useState('');
  const [amount, setAmount] = useState(1000);
  const [reason, setReason] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const fetchRefunds = async () => {
    const res = await api('/refunds/me');
    if (res.success) setRefunds(res.data);
  };

  useEffect(() => {
    fetchRefunds();
  }, []);

  const handleRequest = async () => {
    const res = await api('/refunds', 'POST', {
      paymentId,
      amount,
      reason
    });
    if (res.success) {
      setMessage("Refund request submitted successfully!");
      setPaymentId('');
      setReason('');
      fetchRefunds();
    } else {
      setMessage(`Request failed: ${res.detail || 'Limit check failed'}`);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>Refund Portal</Typography>

      {message && (
        <Alert severity="info" sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          {message}
        </Alert>
      )}

      <Paper sx={{ p: 3, borderRadius: 3, mb: 4 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Request Refund</Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField label="Transaction / Payment ID" fullWidth value={paymentId} onChange={e => setPaymentId(e.target.value)} />
          </Grid>
          <Grid item xs={12} sm={2}>
            <TextField label="Amount" type="number" fullWidth value={amount} onChange={e => setAmount(Number(e.target.value))} />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField label="Reason for Refund" fullWidth value={reason} onChange={e => setReason(e.target.value)} />
          </Grid>
          <Grid item xs={12} sm={2}>
            <Button fullWidth variant="contained" onClick={handleRequest}>Request</Button>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Refund Request History</Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Transaction ID</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Reason</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {refunds.map(r => (
              <TableRow key={r.id}>
                <TableCell>{r.createdAt.split('T')[0]}</TableCell>
                <TableCell>{r.paymentId}</TableCell>
                <TableCell>{r.amount} INR</TableCell>
                <TableCell>{r.reason}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{r.status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};
export default MyRefunds;
