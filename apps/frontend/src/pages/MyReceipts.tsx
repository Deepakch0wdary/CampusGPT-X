import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material';

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

export const MyReceipts: React.FC = () => {
  const [receipts, setReceipts] = useState<any[]>([]);

  useEffect(() => {
    api('/receipts/me').then(res => {
      if (res.success) setReceipts(res.data);
    });
  }, []);

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>Official Tax Receipts</Typography>
      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Receipt ID</TableCell>
              <TableCell>Issued Date</TableCell>
              <TableCell align="right">Amount</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {receipts.map(r => (
              <TableRow key={r.id}>
                <TableCell sx={{ fontWeight: 'bold' }}>{r.receiptNumber}</TableCell>
                <TableCell>{r.issuedAt.split('T')[0]}</TableCell>
                <TableCell align="right">{r.amount} INR</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};
export default MyReceipts;
