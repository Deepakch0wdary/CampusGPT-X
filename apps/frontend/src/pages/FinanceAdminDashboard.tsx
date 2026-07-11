import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, CircularProgress,
  Button, List, ListItem, ListItemText, Table, TableHead,
  TableRow, TableCell, TableBody, Chip
} from '@mui/material';
import { Timeline } from '@mui/icons-material';
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

export const FinanceAdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [overview, setOverview] = useState<any>(null);
  const [depts, setDepts] = useState<any[]>([]);
  const [audits, setAudits] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchOverview = async () => {
    try {
      const [ovRes, deptRes, audRes] = await Promise.all([
        api('/analytics/overview'),
        api('/analytics/departments'),
        api('/audit')
      ]);
      if (ovRes.success) setOverview(ovRes.data);
      if (deptRes.success) setDepts(deptRes.data);
      if (audRes.success) setAudits(audRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading) {
    return (
      <Box p={4} display="flex" justifyContent="center">
        <CircularProgress />
      </Box>
    );
  }

  const o = overview || { totalBilled: 0, totalCollected: 0, totalOutstanding: 0, activeHoldsCount: 0, collectionRate: 0 };

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight="bold" sx={{ mb: 3 }} color="primary">
        Financial Operations Control
      </Typography>

      {/* Metrics Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={3.2}>
          <Card sx={{ bgcolor: 'background.paper', borderRadius: 3, borderLeft: '6px solid #0070f3' }}>
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">Total Billed Dues</Typography>
              <Typography variant="h4" fontWeight="bold">{o.totalBilled} INR</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3.2}>
          <Card sx={{ bgcolor: 'background.paper', borderRadius: 3, borderLeft: '6px solid #4caf50' }}>
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">Total Revenue Collected</Typography>
              <Typography variant="h4" fontWeight="bold">{o.totalCollected} INR</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3.2}>
          <Card sx={{ bgcolor: 'background.paper', borderRadius: 3, borderLeft: '6px solid #f44336' }}>
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">Outstanding Balance</Typography>
              <Typography variant="h4" fontWeight="bold" color="error">{o.totalOutstanding} INR</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={2.4}>
          <Card sx={{ bgcolor: 'background.paper', borderRadius: 3, borderLeft: '6px solid #ff9800' }}>
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">Collection Rate</Typography>
              <Typography variant="h4" fontWeight="bold">{o.collectionRate}%</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Control Buttons */}
      <Paper sx={{ p: 2, mb: 4, display: 'flex', gap: 2, flexWrap: 'wrap', borderRadius: 3 }}>
        <Button variant="contained" onClick={() => navigate('/fee-structures-mgr')}>Structures</Button>
        <Button variant="contained" onClick={() => navigate('/invoices-mgr')}>Invoices</Button>
        <Button variant="contained" onClick={() => navigate('/payments-mgr')}>Collect Payment</Button>
        <Button variant="contained" onClick={() => navigate('/scholarships-mgr')}>Scholarships</Button>
        <Button variant="contained" onClick={() => navigate('/refunds-mgr')}>Refunds Log</Button>
        <Button variant="contained" onClick={() => navigate('/holds-mgr')}>Holds Management</Button>
        <Button variant="outlined" startIcon={<Timeline />} onClick={() => navigate('/finance-analytics')}>Analytics</Button>
      </Paper>

      <Grid container spacing={3}>
        {/* Department analytics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Department Revenue</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Department</TableCell>
                  <TableCell>Billed</TableCell>
                  <TableCell>Collected</TableCell>
                  <TableCell>Rate</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {depts.map((d, index) => (
                  <TableRow key={index}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{d.departmentName}</TableCell>
                    <TableCell>{d.billed} INR</TableCell>
                    <TableCell>{d.collected} INR</TableCell>
                    <TableCell>
                      <Chip label={`${d.collectionRate}%`} color={d.collectionRate > 80 ? 'success' : 'warning'} size="small" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        {/* Financial Audit Trail */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Financial Audit Log</Typography>
            <List sx={{ maxHeight: 350, overflowY: 'auto' }}>
              {audits.map((a) => (
                <ListItem key={a.id} divider sx={{ py: 1 }}>
                  <ListItemText
                    primary={`${a.action} - ${a.entityType}`}
                    secondary={`${a.newData} | Date: ${a.createdAt.split('T')[0]}`}
                    primaryTypographyProps={{ fontSize: 13, fontWeight: 'bold' }}
                    secondaryTypographyProps={{ fontSize: 11 }}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
