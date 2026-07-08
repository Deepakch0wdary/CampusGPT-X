import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, LinearProgress,
  Button, Stack, Chip, CircularProgress, IconButton, Tooltip, Alert
} from '@mui/material';
import {
  Work, TrendingUp, CheckCircle, Person,
  Code, Lightbulb, Refresh, ArrowForward,
  EmojiEvents, Timeline, BarChart, BusinessCenter
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';


const api = async (path: string, method = 'GET', body?: any) => {
  const token = localStorage.getItem('access_token');
  const res = await fetch(`/api/v1/placements${path}`, {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const data = await res.json();
  return data;
};

const scoreColor = (score: number) => {
  if (score >= 75) return '#4caf50';
  if (score >= 50) return '#ff9800';
  if (score >= 25) return '#f44336';
  return '#9e9e9e';
};

const eligibilityColor = (status: string) => {
  switch (status) {
    case 'ELIGIBLE': return 'success';
    case 'INELIGIBLE': return 'error';
    default: return 'default';
  }
};

const PlacementDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<any>(null);
  const [recs, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAll = async () => {
    try {
      const [dashRes, recRes] = await Promise.all([
        api('/dashboard/me'),
        api('/recommendations/me')
      ]);
      if (dashRes.success) setDashboard(dashRes.data);
      if (recRes.success) setRecs(recRes.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleRefreshMatches = async () => {
    setRefreshing(true);
    await api('/matches/recalculate/me', 'POST');
    await fetchAll();
  };

  if (loading) {
    return (
      <Box p={4} display="flex" flexDirection="column" alignItems="center" gap={2}>
        <CircularProgress size={48} />
        <Typography color="text.secondary">Loading Career Intelligence Dashboard...</Typography>
      </Box>
    );
  }

  const d = dashboard || {};
  const completeness = d.profileCompleteness || 0;

  const getPriorityColor = (p: string) => {
    switch (p) {
      case 'CRITICAL': return '#b71c1c';
      case 'HIGH': return '#f44336';
      case 'MEDIUM': return '#ff9800';
      default: return '#4caf50';
    }
  };

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary" gutterBottom>
            Career Intelligence Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Powered by <strong>LOCAL_EXPLAINABLE_CAREER_MATCHING</strong> — deterministic, transparent, no protected attributes used.
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Tooltip title="Recalculate all match scores">
            <IconButton onClick={handleRefreshMatches} disabled={refreshing} color="primary">
              {refreshing ? <CircularProgress size={20} /> : <Refresh />}
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<Work />}
            onClick={() => navigate('/placements/opportunities')}
          >
            Browse Opportunities
          </Button>
        </Stack>
      </Box>

      {/* Disclaimer */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>Intelligence Engine:</strong> All career matching, eligibility evaluation, and skill gap analysis uses
        LOCAL_EXPLAINABLE_CAREER_MATCHING — a deterministic, rule-based engine. No ML model, no LLM, no external AI.
        Protected attributes (religion, caste, gender, disability, etc.) are never used.
      </Alert>

      {/* KPI Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={6} sm={3}>
          <Card raised sx={{ background: 'linear-gradient(135deg, #1a237e, #283593)', color: '#fff' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ opacity: 0.8 }}>Profile Completeness</Typography>
              <Typography variant="h3" fontWeight="bold">{completeness}%</Typography>
              <LinearProgress
                variant="determinate"
                value={completeness}
                sx={{ mt: 1, bgcolor: 'rgba(255,255,255,0.2)', '& .MuiLinearProgress-bar': { bgcolor: '#fff' }, height: 6, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card raised sx={{ background: 'linear-gradient(135deg, #004d40, #00695c)', color: '#fff' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ opacity: 0.8 }}>Skills</Typography>
              <Typography variant="h3" fontWeight="bold">{d.skillCount || 0}</Typography>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>listed in profile</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card raised sx={{ background: 'linear-gradient(135deg, #4a148c, #6a1b9a)', color: '#fff' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ opacity: 0.8 }}>Applications</Typography>
              <Typography variant="h3" fontWeight="bold">{d.totalApplications || 0}</Typography>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>{d.activeApplications || 0} active</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card raised sx={{ background: 'linear-gradient(135deg, #bf360c, #d84315)', color: '#fff' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ opacity: 0.8 }}>Offers Pending</Typography>
              <Typography variant="h3" fontWeight="bold">{d.pendingOffers || 0}</Typography>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>awaiting response</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Top Matches */}
        <Grid item xs={12} md={7}>
          <Paper elevation={3} sx={{ p: 3, borderRadius: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" fontWeight="bold">
                <TrendingUp sx={{ verticalAlign: 'middle', mr: 1 }} />
                Top Job Matches
              </Typography>
              <Button size="small" onClick={() => navigate('/placements/opportunities')} endIcon={<ArrowForward />}>
                View All
              </Button>
            </Box>
            {d.topMatches?.length > 0 ? (
              <Stack spacing={2}>
                {d.topMatches.map((m: any, i: number) => (
                  <Box
                    key={m.opportunityId}
                    sx={{
                      p: 2, borderRadius: 2, border: '1px solid',
                      borderColor: 'divider',
                      background: i === 0 ? 'linear-gradient(90deg, rgba(33,150,243,0.05), transparent)' : 'transparent',
                      display: 'flex', alignItems: 'center', gap: 2
                    }}
                  >
                    <Box
                      sx={{
                        width: 52, height: 52, borderRadius: '50%',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: `conic-gradient(${scoreColor(m.score)} ${m.score * 3.6}deg, #e0e0e0 0deg)`,
                        flexShrink: 0
                      }}
                    >
                      <Box sx={{ width: 38, height: 38, borderRadius: '50%', bgcolor: 'background.paper', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Typography variant="caption" fontWeight="bold">{m.score?.toFixed(0)}%</Typography>
                      </Box>
                    </Box>
                    <Box flex={1} minWidth={0}>
                      <Typography variant="body2" fontWeight="bold" noWrap>{m.opportunityTitle}</Typography>
                      <Typography variant="caption" color="text.secondary">{m.companyName}</Typography>
                    </Box>
                    <Chip
                      label={m.eligibilityStatus}
                      size="small"
                      color={eligibilityColor(m.eligibilityStatus) as any}
                    />
                  </Box>
                ))}
              </Stack>
            ) : (
              <Box textAlign="center" py={4}>
                <Work sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography color="text.secondary">No matches computed yet.</Typography>
                <Button variant="outlined" sx={{ mt: 2 }} onClick={handleRefreshMatches}>
                  Compute Matches
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Recommendations */}
        <Grid item xs={12} md={5}>
          <Paper elevation={3} sx={{ p: 3, borderRadius: 3, height: '100%' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              <Lightbulb sx={{ verticalAlign: 'middle', mr: 1, color: '#ff9800' }} />
              Career Recommendations
            </Typography>
            {recs.length > 0 ? (
              <Stack spacing={1.5} sx={{ maxHeight: 360, overflowY: 'auto' }}>
                {recs.map((r: any) => (
                  <Box
                    key={r.id}
                    sx={{
                      p: 1.5, borderRadius: 2,
                      borderLeft: `4px solid ${getPriorityColor(r.priority)}`,
                      bgcolor: 'action.hover'
                    }}
                  >
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                      <Typography variant="body2" fontWeight="bold">{r.title}</Typography>
                      <Chip label={r.priority} size="small" sx={{ bgcolor: getPriorityColor(r.priority), color: '#fff', fontSize: '0.6rem' }} />
                    </Box>
                    <Typography variant="caption" color="text.secondary">{r.description}</Typography>
                  </Box>
                ))}
              </Stack>
            ) : (
              <Box textAlign="center" py={3}>
                <CheckCircle sx={{ fontSize: 40, color: '#4caf50' }} />
                <Typography variant="body2" color="text.secondary" mt={1}>
                  All recommendations completed!
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>Quick Actions</Typography>
            <Grid container spacing={2}>
              {[
                { label: 'Update Career Profile', icon: <Person />, path: '/placements/profile', color: '#1976d2' },
                { label: 'Manage Skills', icon: <Code />, path: '/placements/skills', color: '#388e3c' },
                { label: 'Browse Opportunities', icon: <BusinessCenter />, path: '/placements/opportunities', color: '#7b1fa2' },
                { label: 'My Applications', icon: <Timeline />, path: '/placements/applications', color: '#f57c00' },
                { label: 'Skill Gap Analysis', icon: <BarChart />, path: '/placements/skill-gap', color: '#c62828' },
                { label: 'Career Goals', icon: <EmojiEvents />, path: '/placements/goals', color: '#00796b' },
              ].map((a) => (
                <Grid item xs={6} sm={4} md={2} key={a.label}>
                  <Button
                    variant="outlined"
                    fullWidth
                    sx={{ flexDirection: 'column', py: 2, gap: 1, borderColor: a.color, color: a.color, '&:hover': { bgcolor: `${a.color}11` } }}
                    onClick={() => navigate(a.path)}
                  >
                    <Box sx={{ color: a.color }}>{a.icon}</Box>
                    <Typography variant="caption" textAlign="center">{a.label}</Typography>
                  </Button>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PlacementDashboard;
