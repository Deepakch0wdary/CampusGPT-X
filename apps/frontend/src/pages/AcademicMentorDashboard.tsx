import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, LinearProgress, Button, Stack
} from '@mui/material';
import {
  Warning, AutoStories, ListAlt, AssignmentTurnedIn, Lightbulb
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const AcademicMentorDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/me/overview', {
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

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography mt={2}>Loading Academic Mentor Dashboard...</Typography>
      </Box>
    );
  }

  const profile = data?.profile || {};
  const stats = data?.stats || {};
  const assessment = data?.assessment || {};

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
      <Typography variant="h4" gutterBottom fontWeight="bold" color="primary">
        Academic Mentor & Intelligence
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Get personalized explainable risk analysis, goals, and customized study plan suggestions.
      </Typography>

      <Grid container spacing={3} mt={1}>
        {/* Risk Card */}
        <Grid item xs={12} md={6}>
          <Card raised sx={{ borderLeft: `6px solid ${getRiskColor(profile.currentRiskLevel)}` }}>
            <CardContent>
              <Typography variant="h6" color="textSecondary">Current Advisory Risk Assessment</Typography>
              <Box display="flex" alignItems="center" gap={2} mt={2}>
                <Typography variant="h3" fontWeight="bold" style={{ color: getRiskColor(profile.currentRiskLevel) }}>
                  {profile.currentRiskLevel}
                </Typography>
                {profile.currentRiskLevel !== 'INSUFFICIENT_DATA' && (
                  <Typography variant="h4" color="textSecondary">
                    ({profile.currentRiskScore}/100)
                  </Typography>
                )}
              </Box>
              <Typography variant="body2" color="textSecondary" mt={2}>
                {assessment.explanation || 'Insufficient academic records available to perform automated analytics.'}
              </Typography>

              <Box mt={3}>
                <Typography variant="body2" fontWeight="bold" gutterBottom>
                  Academic Data Completeness: {profile.dataCompleteness}%
                </Typography>
                <LinearProgress variant="determinate" value={profile.dataCompleteness} color="primary" sx={{ height: 8, borderRadius: 4 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Stats Grid */}
        <Grid item xs={12} md={6}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }} elevation={2}>
                <Typography variant="subtitle2" color="textSecondary">Attendance</Typography>
                <Typography variant="h4" fontWeight="bold" mt={1} color={stats.overallAttendance >= 75 ? 'success.main' : 'error.main'}>
                  {stats.overallAttendance}%
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {stats.overallAttendance >= 75 ? 'Satisfactory' : 'Below 75% limit'}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }} elevation={2}>
                <Typography variant="subtitle2" color="textSecondary">Pending Work</Typography>
                <Typography variant="h4" fontWeight="bold" mt={1} color="warning.main">
                  {stats.pendingAssignments}
                </Typography>
                <Typography variant="caption" color="textSecondary">Assignments</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }} elevation={2}>
                <Typography variant="subtitle2" color="textSecondary">Latest GPA</Typography>
                <Typography variant="h4" fontWeight="bold" mt={1} color="primary">
                  {stats.latestSGPA ? stats.latestSGPA : 'N/A'}
                </Typography>
                <Typography variant="caption" color="textSecondary">Semester SGPA</Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Quick actions stack */}
          <Paper sx={{ p: 2.5, mt: 2 }} elevation={2}>
            <Typography variant="h6" gutterBottom>Academic Planner Actions</Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap mt={1}>
              <Button variant="outlined" startIcon={<Lightbulb />} onClick={() => navigate('/academic-mentor/insights')}>
                Insights
              </Button>
              <Button variant="outlined" startIcon={<Warning />} onClick={() => navigate('/academic-mentor/risk')}>
                Risk Details
              </Button>
              <Button variant="outlined" startIcon={<ListAlt />} onClick={() => navigate('/academic-mentor/recommendations')}>
                Recommendations
              </Button>
              <Button variant="outlined" startIcon={<AutoStories />} onClick={() => navigate('/academic-mentor/study-planner')}>
                Study Plans
              </Button>
              <Button variant="outlined" startIcon={<AssignmentTurnedIn />} onClick={() => navigate('/academic-mentor/goals')}>
                My Goals
              </Button>
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default AcademicMentorDashboard;
