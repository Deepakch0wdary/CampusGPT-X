import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Button, Alert } from '@mui/material';

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

export const ScholarshipPortal: React.FC = () => {
  const [schemes, setSchemes] = useState<any[]>([]);
  const [apps, setApps] = useState<any[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const fetchScholarships = async () => {
    const sRes = await api('/scholarships');
    const aRes = await api('/scholarship-applications/me');
    if (sRes.success) setSchemes(sRes.data);
    if (aRes.success) setApps(aRes.data);
  };

  useEffect(() => {
    fetchScholarships();
  }, []);

  const handleApply = async (schemeId: string) => {
    const res = await api(`/scholarships/${schemeId}/apply`, 'POST');
    if (res.success) {
      setMessage("Your scholarship application was submitted successfully!");
      fetchScholarships();
    } else {
      setMessage(`Application error: ${res.detail || 'Student is not eligible'}`);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>Scholarship & Grants Portal</Typography>

      {message && (
        <Alert severity="info" sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          {message}
        </Alert>
      )}

      {/* Available schemes */}
      <Paper sx={{ p: 3, borderRadius: 3, mb: 4 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Eligible Schemes</Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Scheme Name</TableCell>
              <TableCell>Scholarship Type</TableCell>
              <TableCell>Eligibility Criteria</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {schemes.map(s => (
              <TableRow key={s.id}>
                <TableCell sx={{ fontWeight: 'bold' }}>{s.name}</TableCell>
                <TableCell>{s.type}</TableCell>
                <TableCell>{s.eligibility || 'Open Scheme'}</TableCell>
                <TableCell align="right">
                  <Button variant="contained" size="small" onClick={() => handleApply(s.id)}>Apply</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* Submitted applications */}
      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>My Applications</Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Remarks</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {apps.map(a => (
              <TableRow key={a.id}>
                <TableCell>{a.createdAt.split('T')[0]}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{a.status}</TableCell>
                <TableCell>{a.remarks || 'Under Review'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};
export default ScholarshipPortal;
