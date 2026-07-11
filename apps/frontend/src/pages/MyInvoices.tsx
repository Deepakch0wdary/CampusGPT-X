import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Button, Chip } from '@mui/material';
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

export const MyInvoices: React.FC = () => {
  const [invoices, setInvoices] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    api('/invoices/me').then(res => {
      if (res.success) setInvoices(res.data);
    });
  }, []);

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>My Invoices Registry</Typography>
      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Invoice Number</TableCell>
              <TableCell>Due Date</TableCell>
              <TableCell>Total Amount</TableCell>
              <TableCell>Outstanding Balance</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {invoices.map(i => (
              <TableRow key={i.id}>
                <TableCell sx={{ fontWeight: 'bold' }}>{i.invoiceNumber}</TableCell>
                <TableCell>{i.dueDate.split('T')[0]}</TableCell>
                <TableCell>{i.totalAmount} INR</TableCell>
                <TableCell color="error">{i.balanceAmount} INR</TableCell>
                <TableCell>
                  <Chip label={i.status} color={i.status === 'PAID' ? 'success' : 'warning'} size="small" />
                </TableCell>
                <TableCell align="right">
                  <Button variant="outlined" size="small" onClick={() => navigate(`/invoice/${i.id}`)}>View & Pay</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};
export default MyInvoices;
