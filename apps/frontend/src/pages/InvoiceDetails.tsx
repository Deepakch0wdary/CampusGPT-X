import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import {
  Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody,
  Button, Grid, Alert, Divider, Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem
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

export const InvoiceDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [inv, setInv] = useState<any>(null);
  const [openPay, setOpenPay] = useState(false);
  const [openInst, setOpenInst] = useState(false);
  const [payAmount, setPayAmount] = useState(0);
  const [method, setMethod] = useState('UPI');
  const [installments, setInstallments] = useState(3);
  const [message, setMessage] = useState<string | null>(null);

  const fetchInvoice = async () => {
    const res = await api(`/invoices/${id}`);
    if (res.success) {
      setInv(res.data);
      setPayAmount(res.data.balanceAmount);
    }
  };

  useEffect(() => {
    fetchInvoice();
  }, [id]);

  const handlePay = async () => {
    const res = await api('/payments/demo', 'POST', {
      invoiceId: id,
      amount: payAmount,
      method,
      idempotencyKey: `invoice-pay-${id}-${Date.now()}`
    });
    if (res.success) {
      setOpenPay(false);
      setMessage(`Simulated Payment of ${payAmount} INR processed successfully!`);
      fetchInvoice();
    } else {
      setMessage(`Payment failed: ${res.detail || 'Limit / verification failure'}`);
    }
  };

  const handleSetupInstallment = async () => {
    const res = await api('/installment-plans', 'POST', {
      invoiceId: id,
      name: "Custom Student Installments",
      numberOfInstallments: installments
    });
    if (res.success) {
      setOpenInst(false);
      setMessage(`Active Installment Plan created successfully for ${installments} splits!`);
      fetchInvoice();
    } else {
      setMessage(`Setup failed: ${res.detail}`);
    }
  };

  if (!inv) return <Typography p={3}>Loading Invoice details...</Typography>;

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>Invoice Detailed Statement</Typography>

      {message && (
        <Alert severity="info" sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          {message}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, borderRadius: 3, mb: 3 }}>
            <Typography variant="h6" fontWeight="bold">Invoice Breakdown</Typography>
            <Divider sx={{ my: 2 }} />
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Component Name</TableCell>
                  <TableCell>Code</TableCell>
                  <TableCell align="right">Amount</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {inv.items.map((item: any) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.componentName}</TableCell>
                    <TableCell>{item.componentCode}</TableCell>
                    <TableCell align="right">{item.amount} INR</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Summary Details</Typography>
            <Divider sx={{ mb: 2 }} />
            <Typography>Invoice No: <b>{inv.invoiceNumber}</b></Typography>
            <Typography sx={{ mt: 1 }}>Subtotal: {inv.subtotal} INR</Typography>
            {inv.scholarshipAmount > 0 && <Typography sx={{ color: 'success.main' }}>Scholarship: -{inv.scholarshipAmount} INR</Typography>}
            {inv.discountAmount > 0 && <Typography sx={{ color: 'success.main' }}>Concessions: -{inv.discountAmount} INR</Typography>}
            <Typography variant="h6" sx={{ mt: 2, fontWeight: 'bold' }}>Total Dues: {inv.totalAmount} INR</Typography>
            <Typography sx={{ color: 'error.main', fontWeight: 'bold', mt: 1 }}>Remaining Balance: {inv.balanceAmount} INR</Typography>

            <Divider sx={{ my: 2 }} />

            {inv.balanceAmount > 0 ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button variant="contained" fullWidth color="primary" onClick={() => setOpenPay(true)}>
                  Pay Online (Simulated)
                </Button>
                {inv.status !== 'INSTALLMENT' && (
                  <Button variant="outlined" fullWidth onClick={() => setOpenInst(true)}>
                    Setup Installments
                  </Button>
                )}
              </Box>
            ) : (
              <Alert severity="success">Invoice fully paid.</Alert>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Pay dialog */}
      <Dialog open={openPay} onClose={() => setOpenPay(false)}>
        <DialogTitle>Make Simulated Payment</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Alert severity="warning" sx={{ mb: 2 }}>DEMO PAYMENT - NO REAL MONEY MOVED</Alert>
          <TextField
            label="Payment Amount (INR)"
            type="number"
            fullWidth
            value={payAmount}
            onChange={e => setPayAmount(Number(e.target.value))}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            label="Method"
            select
            fullWidth
            value={method}
            onChange={e => setMethod(e.target.value)}
          >
            <MenuItem value="UPI">UPI Transfer</MenuItem>
            <MenuItem value="CASH">Cash</MenuItem>
            <MenuItem value="CREDIT_CARD">Credit Card</MenuItem>
            <MenuItem value="DEBIT_CARD">Debit Card</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPay(false)}>Cancel</Button>
          <Button variant="contained" onClick={handlePay}>Confirm Payment</Button>
        </DialogActions>
      </Dialog>

      {/* Installment Dialog */}
      <Dialog open={openInst} onClose={() => setOpenInst(false)}>
        <DialogTitle>Setup Installment Schedule</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Typography sx={{ mb: 2 }}>
            Break down the remaining balance of <b>{inv.balanceAmount} INR</b> into monthly installments.
          </Typography>
          <TextField
            label="Number of Installments"
            type="number"
            fullWidth
            value={installments}
            onChange={e => setInstallments(Number(e.target.value))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenInst(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSetupInstallment}>Create Plan</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
export default InvoiceDetails;
