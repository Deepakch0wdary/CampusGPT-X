import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, Button, LinearProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Alert
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const RiskAssessment: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchRisk = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/me/risk-assessment', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success) {
          setData(payload.data);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    setRecalculating(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/me/recalculate', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const payload = await res.json();
      if (res.ok) {
        setSuccessMsg("Risk parameters recalculated successfully.");
        fetchRisk();
      } else {
        setErrorMsg(payload.message || "Failed to trigger recalculation.");
      }
    } catch (e) {
      setErrorMsg("Network error occurred during recalculation.");
    } finally {
      setRecalculating(false);
    }
  };

  useEffect(() => {
    fetchRisk();
  }, []);

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography mt={2}>Loading Academic Risk Assessment...</Typography>
      </Box>
    );
  }

  const assessment = data?.assessment || {};
  const factors = data?.factors || [];

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return '#4caf50';
      case 'MODERATE': return '#ff9800';
      case 'HIGH': return '#f44336';
      case 'CRITICAL': return '#b71c1c';
      default: return '#757575';
    }
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2} mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary">
            Explainable Risk Assessment
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Review the exact weighted factors contributing to your academic support status.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={handleRecalculate}
          disabled={recalculating}
        >
          {recalculating ? 'Recalculating...' : 'Request Recalculation'}
        </Button>
      </Box>

      {successMsg && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMsg(null)}>{successMsg}</Alert>}
      {errorMsg && <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setErrorMsg(null)}>{errorMsg}</Alert>}

      <Grid container spacing={3}>
        {/* Summary Card */}
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Assessment Snapshot
              </Typography>
              <Box my={3} display="flex" flexDirection="column" alignItems="center">
                <Box
                  width={120}
                  height={120}
                  borderRadius="50%"
                  display="flex"
                  flexDirection="column"
                  alignItems="center"
                  justifyContent="center"
                  style={{ border: `8px solid ${getRiskColor(assessment.level)}` }}
                >
                  <Typography variant="h4" fontWeight="bold" style={{ color: getRiskColor(assessment.level) }}>
                    {assessment.score || 0}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">out of 100</Typography>
                </Box>
                <Typography variant="h5" fontWeight="bold" mt={2} style={{ color: getRiskColor(assessment.level) }}>
                  {assessment.level || 'INSUFFICIENT_DATA'}
                </Typography>
              </Box>

              <Typography variant="body2" color="textSecondary" align="center">
                {assessment.explanation}
              </Typography>

              <Box mt={3}>
                <Typography variant="caption" display="block" color="textSecondary">
                  Calculated: {assessment.assessedAt ? new Date(assessment.assessedAt).toLocaleString() : 'Never'}
                </Typography>
                <Typography variant="caption" display="block" color="textSecondary">
                  Version: {assessment.version || 1}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Factors Breakdown */}
        <Grid item xs={12} md={8}>
          <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Factor Contribution Breakdown</Typography>
            {factors.length === 0 ? (
              <Box p={4} textAlign="center">
                <Typography color="textSecondary">No active risk factors found.</Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Factor Code</TableCell>
                      <TableCell align="right">Observed Value</TableCell>
                      <TableCell align="right">Max Weight</TableCell>
                      <TableCell align="right">Contribution Score</TableCell>
                      <TableCell>Impact Explanation</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {factors.map((f: any) => (
                      <TableRow key={f.id}>
                        <TableCell sx={{ fontWeight: '600' }}>{f.factorName}</TableCell>
                        <TableCell align="right">{f.observedValue}</TableCell>
                        <TableCell align="right">{f.weight}</TableCell>
                        <TableCell align="right" style={{ color: f.contribution > 0 ? '#f44336' : '#4caf50', fontWeight: 'bold' }}>
                          +{f.contribution}
                        </TableCell>
                        <TableCell>{f.explanation}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>
      </Grid>

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default RiskAssessment;
