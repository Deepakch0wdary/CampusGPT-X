import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, Button, LinearProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Alert, Stack, Pagination
} from '@mui/material';
import { History, Sync } from '@mui/icons-material';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const AcademicIntelligenceAdmin: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [audits, setAudits] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchAnalytics = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/analytics', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success) {
          setAnalytics(payload.data);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAudits = async (p: number = 1) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/academic-mentor/audits?page=${p}&limit=10`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success) {
          setAudits(payload.data.audits || []);
          setTotalCount(payload.data.total || 0);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleBulkRecalculate = async () => {
    setRecalculating(true);
    setSuccessMsg(null);
    setErrorMsg(null);
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/recalculate', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const payload = await res.json();
      if (res.ok) {
        setSuccessMsg(`Bulk recalculation completed. Processed: ${payload.data.processed}, Failed: ${payload.data.failed}.`);
        fetchAnalytics();
        fetchAudits(1);
      } else {
        setErrorMsg(payload.message || "Failed to trigger bulk recalculation.");
      }
    } catch (e) {
      setErrorMsg("Network error occurred.");
    } finally {
      setRecalculating(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      await Promise.all([fetchAnalytics(), fetchAudits(1)]);
      setLoading(false);
    };
    init();
  }, []);

  const handlePageChange = (_: any, value: number) => {
    setPage(value);
    fetchAudits(value);
  };

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography mt={2}>Loading Admin Academic Intelligence...</Typography>
      </Box>
    );
  }

  const distribution = analytics?.distribution || {};

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2} mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary">Academic Intelligence Admin Panel</Typography>
          <Typography variant="subtitle1" color="textSecondary">Monitor campus risk metrics, coverage metrics, and trigger campus-wide syncs.</Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Sync />}
          onClick={handleBulkRecalculate}
          disabled={recalculating}
        >
          {recalculating ? 'Processing Bulk Recalculation...' : 'Run Bulk Recalculation'}
        </Button>
      </Box>

      {successMsg && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMsg(null)}>{successMsg}</Alert>}
      {errorMsg && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setErrorMsg(null)}>{errorMsg}</Alert>}

      <Grid container spacing={3} mb={4}>
        {/* Coverage Cards */}
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="textSecondary">Students Evaluated</Typography>
              <Typography variant="h3" fontWeight="bold" color="primary" mt={1}>
                {analytics?.totalEvaluated || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="textSecondary">Avg Advisory Risk Score</Typography>
              <Typography variant="h3" fontWeight="bold" color="warning.main" mt={1}>
                {analytics?.averageRiskScore || 0}/100
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle2" color="textSecondary" gutterBottom>Risk Distribution</Typography>
            <Stack direction="row" spacing={1} mt={1} justifyContent="space-between" flexWrap="wrap">
              <Box>
                <Typography variant="h6" fontWeight="bold" color="success.main">{distribution.LOW || 0}</Typography>
                <Typography variant="caption" color="textSecondary">LOW</Typography>
              </Box>
              <Box>
                <Typography variant="h6" fontWeight="bold" color="warning.main">{distribution.MODERATE || 0}</Typography>
                <Typography variant="caption" color="textSecondary">MODERATE</Typography>
              </Box>
              <Box>
                <Typography variant="h6" fontWeight="bold" color="error.main">{distribution.HIGH || 0}</Typography>
                <Typography variant="caption" color="textSecondary">HIGH</Typography>
              </Box>
              <Box>
                <Typography variant="h6" fontWeight="bold" color="error.dark">{distribution.CRITICAL || 0}</Typography>
                <Typography variant="caption" color="textSecondary">CRITICAL</Typography>
              </Box>
              <Box>
                <Typography variant="h6" fontWeight="bold" color="textSecondary">{distribution.INSUFFICIENT_DATA || 0}</Typography>
                <Typography variant="caption" color="textSecondary">NO DATA</Typography>
              </Box>
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      {/* Audits Table */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="h6" display="flex" alignItems="center" gap={1} gutterBottom>
          <History /> Mentoring Privileged Action Audits
        </Typography>
        <TableContainer sx={{ mt: 2 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Actor ID</TableCell>
                <TableCell>Student ID</TableCell>
                <TableCell>Action Type</TableCell>
                <TableCell>Entity Type</TableCell>
                <TableCell>Metadata Summary</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {audits.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">No recent privileged action logs found.</TableCell>
                </TableRow>
              ) : (
                audits.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>{new Date(a.createdAt).toLocaleString()}</TableCell>
                    <TableCell>{a.actorId || 'System'}</TableCell>
                    <TableCell>{a.studentId || 'N/A'}</TableCell>
                    <TableCell sx={{ fontWeight: '600' }}>{a.action}</TableCell>
                    <TableCell>{a.entityType}</TableCell>
                    <TableCell>{a.actionMetadata || 'None'}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <Box display="flex" justifyContent="center" mt={3}>
          <Pagination
            count={Math.ceil(totalCount / 10)}
            page={page}
            onChange={handlePageChange}
            color="primary"
          />
        </Box>
      </Paper>

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default AcademicIntelligenceAdmin;
