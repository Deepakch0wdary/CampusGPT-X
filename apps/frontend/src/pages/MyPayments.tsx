import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Chip } from '@mui/material';

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

export const MyPayments: React.FC = () => {
  const [payments, setPayments] = useState<any[]>([]);

  useEffect(() => {
    api('/payments/me').then(res => {
      if (res.success) setPayments(res.data);
    });
  }, []);

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>My Payment Statements</Typography>
      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Receipt / Payment Number</TableCell>
              <TableCell>Paid Date</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Method</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {payments.map(p => (
              <TableRow key={p.id}>
                <TableCell sx={{ fontWeight: 'bold' }}>{p.paymentNumber}</TableCell>
                <TableCell>{p.paidAt ? p.paidAt.split('T')[0] : 'N/A'}</TableCell>
                <TableCell>{p.amount} INR</TableCell>
                <TableCell>{p.method}</TableCell>
                <TableCell>
                  <Chip label={p.status} color="success" size="small" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};
export default MyPayments;
