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

export const FeeStructureManager: React.FC = () => {
  const [structs, setStructs] = useState<any[]>([]);
  const [open, setOpen] = useState(false);

  // Form fields
  const [ay, setAy] = useState('AY-2026');
  const [prog, setProg] = useState('CSE');
  const [cat, setCat] = useState('REGULAR');
  const [tui, setTui] = useState(50000);
  const [exm, setExm] = useState(10000);

  const fetchStructs = async () => {
    const res = await api('/fee-structures');
    if (res.success) setStructs(res.data);
  };

  useEffect(() => {
    fetchStructs();
  }, []);

  const handleCreate = async () => {
    const payload = {
      academicYearId: ay,
      programId: prog,
      category: cat,
      components: [
        { name: "Tuition Fee", code: "TUI", amount: tui, dueDate: new Date().toISOString() },
        { name: "Examination Fee", code: "EXM", amount: exm, dueDate: new Date().toISOString() }
      ]
    };
    const res = await api('/fee-structures', 'POST', payload);
    if (res.success) {
      setOpen(false);
      fetchStructs();
    }
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" mb={3}>
        <Typography variant="h5" fontWeight="bold">Fee Structure Setup</Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>Create Structure</Button>
      </Box>

      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Academic Year</TableCell>
              <TableCell>Program Code</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Quota</TableCell>
              <TableCell>Currency</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {structs.map(s => (
              <TableRow key={s.id}>
                <TableCell>{s.academicYearId}</TableCell>
                <TableCell>{s.programId}</TableCell>
                <TableCell>{s.category || 'N/A'}</TableCell>
                <TableCell>{s.quota || 'N/A'}</TableCell>
                <TableCell>{s.currency}</TableCell>
                <TableCell>{s.status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Configure Fee Structure</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField label="Academic Year" fullWidth value={ay} onChange={e => setAy(e.target.value)} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Program ID/Code" fullWidth value={prog} onChange={e => setProg(e.target.value)} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Category" fullWidth value={cat} onChange={e => setCat(e.target.value)} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Tuition Amount (INR)" type="number" fullWidth value={tui} onChange={e => setTui(Number(e.target.value))} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Exam Amount (INR)" type="number" fullWidth value={exm} onChange={e => setExm(Number(e.target.value))} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
export default FeeStructureManager;
