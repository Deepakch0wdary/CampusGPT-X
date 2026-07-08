import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, Chip, FormControl, InputLabel, Select, MenuItem, Stack, LinearProgress
} from '@mui/material';
import {
  CheckCircle, ErrorOutline, InfoOutlined, TrendingUp
} from '@mui/icons-material';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const AcademicInsights: React.FC = () => {
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');

  const fetchInsights = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/me/insights', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success) {
          setInsights(payload.data || []);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'STRENGTH': return <CheckCircle color="success" />;
      case 'WEAKNESS': return <ErrorOutline color="error" />;
      case 'TREND': return <TrendingUp color="info" />;
      default: return <InfoOutlined color="primary" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'HIGH': return 'error';
      case 'MEDIUM': return 'warning';
      case 'LOW': return 'info';
      default: return 'default';
    }
  };

  const filteredInsights = insights.filter(i => {
    if (typeFilter !== 'ALL' && i.type !== typeFilter) return false;
    if (severityFilter !== 'ALL' && i.severity !== severityFilter) return false;
    return true;
  });

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography mt={2}>Loading Academic Insights...</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight="bold" color="primary" gutterBottom>
        Academic Insights
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Analyze your strengths, areas of growth, and performance trends detected from class attendance and grades.
      </Typography>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }} elevation={1}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Type</InputLabel>
              <Select value={typeFilter} label="Type" onChange={(e) => setTypeFilter(e.target.value)}>
                <MenuItem value="ALL">All Types</MenuItem>
                <MenuItem value="STRENGTH">Strengths</MenuItem>
                <MenuItem value="WEAKNESS">Weaknesses</MenuItem>
                <MenuItem value="TREND">Trends</MenuItem>
                <MenuItem value="ATTENDANCE">Attendance Concerns</MenuItem>
                <MenuItem value="DEADLINE">Deadline Concerns</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Severity</InputLabel>
              <Select value={severityFilter} label="Severity" onChange={(e) => setSeverityFilter(e.target.value)}>
                <MenuItem value="ALL">All Severities</MenuItem>
                <MenuItem value="INFO">Info</MenuItem>
                <MenuItem value="LOW">Low</MenuItem>
                <MenuItem value="MEDIUM">Medium</MenuItem>
                <MenuItem value="HIGH">High</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {filteredInsights.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">No academic insights match your filter criteria.</Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {filteredInsights.map((insight) => (
            <Grid item xs={12} key={insight.id}>
              <Card variant="outlined">
                <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, '&:last-child': { pb: 2 } }}>
                  <Box display="flex" alignItems="center">
                    {getInsightIcon(insight.type)}
                  </Box>
                  <Box flexGrow={1}>
                    <Stack direction="row" alignItems="center" spacing={1.5} flexWrap="wrap">
                      <Typography variant="h6" fontWeight="600">{insight.title}</Typography>
                      <Chip label={insight.type} size="small" variant="outlined" color="primary" />
                      <Chip label={insight.severity} size="small" color={getSeverityColor(insight.severity)} />
                    </Stack>
                    <Typography variant="body2" color="textSecondary" mt={1}>
                      {insight.summary}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default AcademicInsights;
