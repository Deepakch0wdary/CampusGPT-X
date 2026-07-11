import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, TextField, Button, Table, TableHead,
  TableRow, TableCell, TableBody, Grid, Alert
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

export const FinancialHoldManager: React.FC = () => {
  const [holds, setHolds] = useState<any[]>([]);
  const [studentId, setStudentId] = useState('');
  const [reason, setReason] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const fetchHolds = async () => {
    // Reusing holds query or listing audit logs of holds
    const res = await api('/audit');
    if (res.success) {
      const holdAudits = res.data.filter((a: any) => a.entityType === 'HOLD');
      setHolds(holdAudits);
    }
  };

  useEffect(() => {
    fetchHolds();
  }, []);

  const handlePlaceHold = async () => {
    const res = await api('/holds', 'POST', { studentId, reason });
    if (res.success) {
      setMessage(`Financial hold placed on student ${studentId} successfully.`);
      setStudentId('');
      setReason('');
      fetchHolds();
    } else {
      setMessage(`Error: ${res.detail || 'Failed to place hold'}`);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>Financial holds desk</Typography>

      {message && (
        <Alert severity="info" sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          {message}
        </Alert>
      )}

      <Paper sx={{ p: 3, borderRadius: 3, mb: 4 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Place Active Financial Hold</Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField label="Student Candidate ID" fullWidth value={studentId} onChange={e => setStudentId(e.target.value)} />
          </Grid>
          <Grid item xs={12} sm={5}>
            <TextField label="Reason / Violation" fullWidth value={reason} onChange={e => setReason(e.target.value)} />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button fullWidth variant="contained" color="error" onClick={handlePlaceHold}>
              Place Hold
            </Button>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Audited Holds Log</Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Log ID</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Details</TableCell>
              <TableCell>Operator ID</TableCell>
              <TableCell>Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {holds.map(h => (
              <TableRow key={h.id}>
                <TableCell>{h.id}</TableCell>
                <TableCell sx={{ color: 'error.main', fontWeight: 'bold' }}>{h.action}</TableCell>
                <TableCell>{h.newData}</TableCell>
                <TableCell>{h.userId}</TableCell>
                <TableCell>{h.createdAt.split('T')[0]}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};
export default FinancialHoldManager;
