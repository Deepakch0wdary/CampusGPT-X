import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, FormControl, InputLabel, Select, MenuItem, Stack, LinearProgress, Divider, Alert
} from '@mui/material';
import { TrendingUp, HelpOutline } from '@mui/icons-material';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const ParentAcademicInsights: React.FC = () => {
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<string>('');
  const [childOverview, setChildOverview] = useState<any>(null);
  const [childInsights, setChildInsights] = useState<any[]>([]);
  const [childRecs, setChildRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchChildren = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/children', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success && payload.data && payload.data.length > 0) {
          setChildren(payload.data);
          setSelectedChildId(payload.data[0].id);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchChildDetails = async (studentId: string) => {
    setDetailsLoading(true);
    setErrorMsg(null);
    const token = localStorage.getItem('access_token');
    try {
      // 1. Overview
      const resOverview = await fetch(`/api/v1/academic-mentor/children/${studentId}/overview`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!resOverview.ok) {
        setErrorMsg("Failed to retrieve academic overview for child.");
        return;
      }
      const dataOverview = await resOverview.json();
      setChildOverview(dataOverview.data);

      // 2. Insights
      const resInsights = await fetch(`/api/v1/academic-mentor/children/${studentId}/insights`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resInsights.ok) {
        const dataInsights = await resInsights.json();
        setChildInsights(dataInsights.data || []);
      }

      // 3. Recommendations
      const resRecs = await fetch(`/api/v1/academic-mentor/children/${studentId}/recommendations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resRecs.ok) {
        const dataRecs = await resRecs.json();
        setChildRecs(dataRecs.data || []);
      }

    } catch (e) {
      setErrorMsg("Network error occurred.");
    } finally {
      setDetailsLoading(false);
    }
  };

  useEffect(() => {
    fetchChildren();
  }, []);

  useEffect(() => {
    if (selectedChildId) {
      fetchChildDetails(selectedChildId);
    }
  }, [selectedChildId]);

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography mt={2}>Loading Parent Academic Portal...</Typography>
      </Box>
    );
  }

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
      <Typography variant="h4" fontWeight="bold" color="primary" gutterBottom>
        Parent Portal: Academic Insights
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Select a child below to review their general attendance, result trends, and advisory study suggestions.
      </Typography>

      {children.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 3 }}>
          <Typography color="textSecondary">No verified child profiles are currently linked to your parent account.</Typography>
        </Paper>
      ) : (
        <Box mt={3}>
          <FormControl sx={{ minWidth: 240, mb: 3 }} size="small">
            <InputLabel>Switch Child Profile</InputLabel>
            <Select
              value={selectedChildId}
              label="Switch Child Profile"
              onChange={(e) => setSelectedChildId(e.target.value)}
            >
              {children.map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.name} ({c.relationship})
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {errorMsg && <Alert severity="error" sx={{ mb: 3 }}>{errorMsg}</Alert>}

          {detailsLoading ? (
            <Box py={5} textAlign="center">
              <LinearProgress />
              <Typography mt={2}>Syncing child data...</Typography>
            </Box>
          ) : (
            childOverview && (
              <Grid container spacing={3}>
                {/* Child Overview & Advisory Score */}
                <Grid item xs={12} md={4}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardContent>
                      <Typography variant="h6" color="textSecondary" gutterBottom>
                        Child Academic Status
                      </Typography>
                      <Box my={3} display="flex" flexDirection="column" alignItems="center">
                        <Box
                          width={110}
                          height={110}
                          borderRadius="50%"
                          display="flex"
                          flexDirection="column"
                          alignItems="center"
                          justifyContent="center"
                          style={{ border: `8px solid ${getRiskColor(childOverview.profile?.currentRiskLevel)}` }}
                        >
                          <Typography variant="h5" fontWeight="bold" style={{ color: getRiskColor(childOverview.profile?.currentRiskLevel) }}>
                            {childOverview.profile?.currentRiskLevel || 'N/A'}
                          </Typography>
                        </Box>
                        <Typography variant="body2" color="textSecondary" mt={2} align="center">
                          Advisory academic assessment level.
                        </Typography>
                      </Box>

                      <Divider sx={{ my: 2 }} />

                      <Stack spacing={2}>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2" color="textSecondary">Overall Attendance:</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {childOverview.stats?.overallAttendance}%
                          </Typography>
                        </Box>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2" color="textSecondary">Pending Workloads:</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {childOverview.stats?.pendingAssignments} assignments
                          </Typography>
                        </Box>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2" color="textSecondary">Latest Semester SGPA:</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {childOverview.stats?.latestSGPA || 'N/A'}
                          </Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Growth Areas and Recommendations */}
                <Grid item xs={12} md={8}>
                  <Paper sx={{ p: 2.5, mb: 3 }} variant="outlined">
                    <Typography variant="h6" display="flex" alignItems="center" gap={1} gutterBottom>
                      <TrendingUp /> Strengths & Concerns
                    </Typography>
                    {childInsights.length === 0 ? (
                      <Typography variant="body2" color="textSecondary">No specific strengths or weakness patterns generated.</Typography>
                    ) : (
                      <Stack spacing={1.5} mt={2}>
                        {childInsights.map((insight) => (
                          <Box key={insight.id} p={1.5} border="1px solid #eee" borderRadius={1} bgcolor="#fafafa">
                            <Typography variant="subtitle2" fontWeight="bold">{insight.title}</Typography>
                            <Typography variant="body2" color="textSecondary">{insight.summary}</Typography>
                          </Box>
                        ))}
                      </Stack>
                    )}
                  </Paper>

                  <Paper sx={{ p: 2.5 }} variant="outlined">
                    <Typography variant="h6" display="flex" alignItems="center" gap={1} gutterBottom>
                      <HelpOutline /> Advisory Academic Recommendations
                    </Typography>
                    {childRecs.length === 0 ? (
                      <Typography variant="body2" color="textSecondary">No advisory study plan recommendations configured.</Typography>
                    ) : (
                      <Stack spacing={1.5} mt={2}>
                        {childRecs.map((rec) => (
                          <Box key={rec.id} p={1.5} border="1px solid #eee" borderRadius={1}>
                            <Typography variant="subtitle2" fontWeight="bold" color="primary">{rec.title}</Typography>
                            <Typography variant="body2" color="textSecondary">{rec.description}</Typography>
                            <Typography variant="caption" color="textSecondary" display="block" mt={1}>
                              Reason: {rec.reason}
                            </Typography>
                          </Box>
                        ))}
                      </Stack>
                    )}
                  </Paper>
                </Grid>
              </Grid>
            )
          )}
        </Box>
      )}

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default ParentAcademicInsights;
