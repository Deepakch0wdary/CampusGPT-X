import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, TextField, Button, Table, TableHead,
  TableRow, TableCell, TableBody, Dialog, DialogTitle, DialogContent,
  DialogActions, Grid
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

export const InvoiceManager: React.FC = () => {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [open, setOpen] = useState(false);

  const [studentId, setStudentId] = useState('');
  const [dueDate, setDueDate] = useState('2026-12-31T00:00:00');

  const fetchInvoices = async () => {
    // Reusing get-all invoices logic
    const res = await fetch('/api/v1/invoices', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json());
    if (res.success) setInvoices(res.data);
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const handleGenerate = async () => {
    const res = await api('/invoices', 'POST', {
      studentId,
      dueDate
    });
    if (res.success) {
      setOpen(false);
      fetchInvoices();
    }
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" mb={3}>
        <Typography variant="h5" fontWeight="bold">Invoice registry</Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>Generate Invoice</Button>
      </Box>

      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Invoice Number</TableCell>
              <TableCell>Student ID</TableCell>
              <TableCell>Total Amount</TableCell>
              <TableCell>Paid Amount</TableCell>
              <TableCell>Balance Amount</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {invoices.map(i => (
              <TableRow key={i.id}>
                <TableCell sx={{ fontWeight: 'bold' }}>{i.invoiceNumber}</TableCell>
                <TableCell>{i.studentId}</TableCell>
                <TableCell>{i.totalAmount} INR</TableCell>
                <TableCell>{i.paidAmount} INR</TableCell>
                <TableCell color="error">{i.balanceAmount} INR</TableCell>
                <TableCell>{i.status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Generate Fee Invoice</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField label="Student Candidate ID" fullWidth value={studentId} onChange={e => setStudentId(e.target.value)} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Due Date" fullWidth type="datetime-local" value={dueDate} onChange={e => setDueDate(e.target.value)} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleGenerate}>Generate</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
export default InvoiceManager;
