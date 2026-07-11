import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Button, Table, TableHead, TableRow, TableCell, TableBody
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

export const RefundManager: React.FC = () => {
  const [refunds, setRefunds] = useState<any[]>([]);

  const fetchRefunds = async () => {
    const res = await fetch('/api/v1/refunds', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json());
    if (res.success) setRefunds(res.data);
  };

  useEffect(() => {
    fetchRefunds();
  }, []);

  const handleReview = async (refundId: string, status: string) => {
    const res = await api(`/refunds/${refundId}/status`, 'PATCH', {
      status,
      remarks: `Reviewed by finance desk at ${new Date().toISOString()}`
    });
    if (res.success) {
      fetchRefunds();
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>Refund operations log</Typography>

      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Refund Request ID</TableCell>
              <TableCell>Payment ID</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Reason</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {refunds.map(r => (
              <TableRow key={r.id}>
                <TableCell>{r.id}</TableCell>
                <TableCell>{r.paymentId}</TableCell>
                <TableCell>{r.amount} INR</TableCell>
                <TableCell>{r.reason}</TableCell>
                <TableCell>{r.status}</TableCell>
                <TableCell align="right">
                  {r.status === 'REQUESTED' && (
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                      <Button variant="outlined" color="success" size="small" onClick={() => handleReview(r.id, 'APPROVED')}>Approve</Button>
                      <Button variant="outlined" color="error" size="small" onClick={() => handleReview(r.id, 'REJECTED')}>Reject</Button>
                    </Box>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};
export default RefundManager;
