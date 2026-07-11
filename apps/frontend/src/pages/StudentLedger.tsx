import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Chip
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

export const StudentLedger: React.FC = () => {
  const [entries, setEntries] = useState<any[]>([]);

  const fetchLedger = async () => {
    const res = await api('/ledger/me');
    if (res.success) setEntries(res.data);
  };

  useEffect(() => {
    fetchLedger();
  }, []);

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>Official Student Ledger</Typography>

      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Transaction Type</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Direction</TableCell>
              <TableCell align="right">Amount</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entries.map(e => (
              <TableRow key={e.id}>
                <TableCell>{e.createdAt.split('T')[0]}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{e.type}</TableCell>
                <TableCell>{e.description || 'Adjustment Entry'}</TableCell>
                <TableCell>
                  <Chip
                    label={e.direction}
                    color={e.direction === 'CREDIT' ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', color: e.direction === 'CREDIT' ? 'success.main' : 'error.main' }}>
                  {e.direction === 'CREDIT' ? '+' : '-'}{e.amount} INR
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};
export default StudentLedger;
