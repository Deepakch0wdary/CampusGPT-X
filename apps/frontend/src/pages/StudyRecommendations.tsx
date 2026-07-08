import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, Button, Chip, Stack, LinearProgress, Alert
} from '@mui/material';
import {
  Check, Close, AutoStories
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const StudyRecommendations: React.FC = () => {
  const navigate = useNavigate();
  const [recs, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  const fetchRecs = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/me/recommendations', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success) {
          setRecs(payload.data || []);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (id: string, status: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/academic-mentor/me/recommendations/${id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        setAlert({ type: 'success', msg: `Recommendation marked as ${status}.` });
        fetchRecs();
      } else {
        const payload = await res.json();
        setAlert({ type: 'error', msg: payload.message || "Failed to update recommendation status." });
      }
    } catch (e) {
      setAlert({ type: 'error', msg: "Network error occurred." });
    }
  };

  useEffect(() => {
    fetchRecs();
  }, []);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'HIGH': return 'error';
      case 'MEDIUM': return 'warning';
      default: return 'info';
    }
  };

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography mt={2}>Loading Study Recommendations...</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight="bold" color="primary" gutterBottom>
        Personalized Academic Recommendations
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Review advisory recommendations generated based on your attendance, submission records, and test marks.
      </Typography>

      {alert && <Alert severity={alert.type} sx={{ my: 2 }} onClose={() => setAlert(null)}>{alert.msg}</Alert>}

      {recs.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 2 }}>
          <Typography color="textSecondary">You have no active study recommendations at this time.</Typography>
        </Paper>
      ) : (
        <Grid container spacing={3} mt={1}>
          {recs.map((rec) => (
            <Grid item xs={12} md={6} key={rec.id}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={1}>
                    <Chip label={rec.category} variant="outlined" color="primary" size="small" />
                    <Chip label={`${rec.priority} Priority`} color={getPriorityColor(rec.priority)} size="small" />
                  </Stack>

                  <Typography variant="h6" fontWeight="600" mt={2} gutterBottom>
                    {rec.title}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" paragraph>
                    {rec.description}
                  </Typography>

                  <Paper sx={{ p: 1.5, bgcolor: '#f5f5f5', mt: 2 }} variant="outlined">
                    <Typography variant="caption" display="block" fontWeight="bold" color="textSecondary">
                      REASON FOR SUGGESTION:
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {rec.reason}
                    </Typography>
                  </Paper>

                  <Box mt={1}>
                    <Typography variant="caption" color="textSecondary">
                      Status: <strong>{rec.status}</strong>
                    </Typography>
                  </Box>
                </CardContent>

                <Box p={2} borderTop="1px solid #e0e0e0" display="flex" justifyContent="space-between" alignItems="center">
                  <Stack direction="row" spacing={1}>
                    {rec.status === 'ACTIVE' && (
                      <>
                        <Button
                          size="small"
                          variant="contained"
                          color="success"
                          startIcon={<Check />}
                          onClick={() => handleUpdateStatus(rec.id, 'ACCEPTED')}
                        >
                          Accept
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          color="error"
                          startIcon={<Close />}
                          onClick={() => handleUpdateStatus(rec.id, 'DISMISSED')}
                        >
                          Dismiss
                        </Button>
                      </>
                    )}
                    {rec.status === 'ACCEPTED' && (
                      <Button
                        size="small"
                        variant="contained"
                        color="primary"
                        startIcon={<Check />}
                        onClick={() => handleUpdateStatus(rec.id, 'COMPLETED')}
                      >
                        Complete
                      </Button>
                    )}
                  </Stack>

                  {rec.status === 'ACCEPTED' && (
                    <Button
                      size="small"
                      variant="outlined"
                      color="primary"
                      startIcon={<AutoStories />}
                      onClick={() => navigate('/academic-mentor/study-planner', { state: { recommendation: rec } })}
                    >
                      Study Plan
                    </Button>
                  )}
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default StudyRecommendations;
