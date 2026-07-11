import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Grid
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

export const FinanceAnalytics: React.FC = () => {
  const [collections, setCollections] = useState<any[]>([]);
  const [depts, setDepts] = useState<any[]>([]);

  const fetchAnalytics = async () => {
    const [cRes, dRes] = await Promise.all([
      api('/analytics/collections'),
      api('/analytics/departments')
    ]);
    if (cRes.success) setCollections(cRes.data);
    if (dRes.success) setDepts(dRes.data);
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>Collection Analytics & Forecasting</Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Monthly Revenue Stream</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Billing Month</TableCell>
                  <TableCell align="right">Amount Collected</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {collections.map((c, index) => (
                  <TableRow key={index}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{c.month}</TableCell>
                    <TableCell align="right">{c.amount} INR</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Department Breakdowns</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Department</TableCell>
                  <TableCell align="right">Billed</TableCell>
                  <TableCell align="right">Collected</TableCell>
                  <TableCell align="right">Rate</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {depts.map((d, index) => (
                  <TableRow key={index}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{d.departmentName}</TableCell>
                    <TableCell align="right">{d.billed} INR</TableCell>
                    <TableCell align="right">{d.collected} INR</TableCell>
                    <TableCell align="right">{d.collectionRate}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
export default FinanceAnalytics;
