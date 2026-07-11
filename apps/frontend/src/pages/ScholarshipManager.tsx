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

export const ScholarshipManager: React.FC = () => {
  const [schemes, setSchemes] = useState<any[]>([]);
  const [apps, setApps] = useState<any[]>([]);
  const [open, setOpen] = useState(false);

  // Form fields
  const [name, setName] = useState('');
  const [type, setType] = useState('Merit');
  const [fixedAmount, setFixedAmount] = useState(15000);
  const [eligibility, setEligibility] = useState('MIN_CGPA:8.0');

  const fetchData = async () => {
    const sRes = await api('/scholarships');
    const aRes = await fetch('/api/v1/scholarship-applications', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json());

    if (sRes.success) setSchemes(sRes.data);
    if (aRes.success) setApps(aRes.data);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateScheme = async () => {
    const res = await api('/scholarships', 'POST', {
      name,
      type,
      fixedAmount,
      eligibility,
      validFrom: new Date().toISOString(),
      validTo: new Date(Date.now() + 365*24*60*60*1000).toISOString()
    });
    if (res.success) {
      setOpen(false);
      fetchData();
    }
  };

  const handleReview = async (appId: string, status: string) => {
    const res = await api(`/scholarship-applications/${appId}/status`, 'PATCH', {
      status,
      remarks: `Reviewed by Finance Officer at ${new Date().toISOString()}`
    });
    if (res.success) {
      fetchData();
    }
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" mb={3}>
        <Typography variant="h5" fontWeight="bold">Scholarship schemes & application reviews</Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>Create Scheme</Button>
      </Box>

      {/* Schemes List */}
      <Paper sx={{ p: 3, borderRadius: 3, mb: 4 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Scholarship Schemes</Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Scheme Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Eligibility</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {schemes.map(s => (
              <TableRow key={s.id}>
                <TableCell sx={{ fontWeight: 'bold' }}>{s.name}</TableCell>
                <TableCell>{s.type}</TableCell>
                <TableCell>{s.eligibility}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* Applications list */}
      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Applications List</Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Student ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Remarks</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {apps.map(a => (
              <TableRow key={a.id}>
                <TableCell>{a.studentId}</TableCell>
                <TableCell>{a.status}</TableCell>
                <TableCell>{a.remarks}</TableCell>
                <TableCell align="right">
                  {a.status === 'SUBMITTED' && (
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                      <Button variant="outlined" color="success" size="small" onClick={() => handleReview(a.id, 'APPROVED')}>Approve</Button>
                      <Button variant="outlined" color="error" size="small" onClick={() => handleReview(a.id, 'REJECTED')}>Reject</Button>
                    </Box>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Configure Scholarship Scheme</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField label="Scheme Name" fullWidth value={name} onChange={e => setName(e.target.value)} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Type" fullWidth value={type} onChange={e => setType(e.target.value)} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Amount" type="number" fullWidth value={fixedAmount} onChange={e => setFixedAmount(Number(e.target.value))} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Eligibility (Rules)" fullWidth value={eligibility} onChange={e => setEligibility(e.target.value)} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateScheme}>Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
export default ScholarshipManager;
