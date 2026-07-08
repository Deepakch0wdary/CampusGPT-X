import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, Button, TextField, LinearProgress, List, ListItem, ListItemText, Checkbox, Dialog, DialogTitle, DialogContent, DialogActions, Stack, Alert
} from '@mui/material';
import { Add, CalendarToday, FormatListBulleted } from '@mui/icons-material';
import { useLocation } from 'react-router-dom';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const StudyPlanner: React.FC = () => {
  const location = useLocation();
  const recommendation = location.state?.recommendation;

  const [plans, setPlans] = useState<any[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<any>(null);
  const [selectedPlanItems, setSelectedPlanItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Dialog controls
  const [openCreate, setOpenCreate] = useState(false);
  const [newPlan, setNewPlan] = useState({
    title: recommendation ? `Study Plan: ${recommendation.title}` : '',
    description: recommendation ? `Plan based on advisory recommendation: ${recommendation.description}` : '',
    startDate: new Date().toISOString().split('T')[0],
    endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    taskTitle: recommendation ? recommendation.title : 'Study session',
    taskMinutes: 60
  });

  const [alert, setAlert] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  const fetchPlans = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/me/study-plans', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success) {
          setPlans(payload.data || []);
          if (payload.data && payload.data.length > 0 && !selectedPlan) {
            fetchPlanDetails(payload.data[0].id);
          }
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlanDetails = async (id: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/academic-mentor/me/study-plans/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success) {
          setSelectedPlan(payload.data.plan);
          setSelectedPlanItems(payload.data.items || []);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreatePlan = async () => {
    const token = localStorage.getItem('access_token');
    const payload = {
      title: newPlan.title,
      description: newPlan.description,
      startDate: new Date(newPlan.startDate).toISOString(),
      endDate: new Date(newPlan.endDate).toISOString(),
      generatedFromRecommendationId: recommendation ? recommendation.id : null,
      items: [
        {
          title: newPlan.taskTitle,
          description: "Initial task created for the study plan.",
          scheduledDate: new Date(newPlan.startDate).toISOString(),
          estimatedMinutes: Number(newPlan.taskMinutes),
          orderIndex: 0
        }
      ]
    };

    try {
      const res = await fetch('/api/v1/academic-mentor/me/study-plans', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setAlert({ type: 'success', msg: "Study plan created successfully." });
        setOpenCreate(false);
        fetchPlans();
      } else {
        const errPayload = await res.json();
        setAlert({ type: 'error', msg: errPayload.message || "Failed to create study plan." });
      }
    } catch (e) {
      setAlert({ type: 'error', msg: "Network error occurred." });
    }
  };

  const handleToggleItem = async (itemId: string, currentStatus: string) => {
    const token = localStorage.getItem('access_token');
    const nextStatus = currentStatus === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    try {
      const res = await fetch(`/api/v1/academic-mentor/me/study-plans/items/${itemId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: nextStatus })
      });
      if (res.ok) {
        if (selectedPlan) {
          fetchPlanDetails(selectedPlan.id);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchPlans();
    if (recommendation) {
      setOpenCreate(true);
    }
  }, [recommendation]);

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography mt={2}>Loading Study Planner...</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2} mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary">Study Plans & Planner</Typography>
          <Typography variant="subtitle1" color="textSecondary">Create structured, trackable study schedules from recommendations.</Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setOpenCreate(true)}>
          New Study Plan
        </Button>
      </Box>

      {alert && <Alert severity={alert.type} sx={{ mb: 3 }} onClose={() => setAlert(null)}>{alert.msg}</Alert>}

      <Grid container spacing={3}>
        {/* Left Side: Plans List */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, minHeight: 400 }} variant="outlined">
            <Typography variant="h6" display="flex" alignItems="center" gap={1} gutterBottom>
              <FormatListBulleted /> My Plans
            </Typography>
            {plans.length === 0 ? (
              <Box p={2} textAlign="center">
                <Typography variant="body2" color="textSecondary">No study plans created yet.</Typography>
              </Box>
            ) : (
              <List>
                {plans.map((p) => (
                  <ListItem
                    button
                    key={p.id}
                    selected={selectedPlan && selectedPlan.id === p.id}
                    onClick={() => fetchPlanDetails(p.id)}
                    sx={{ borderRadius: 1, mb: 1 }}
                  >
                    <ListItemText
                      primary={p.title}
                      secondary={`Timeline: ${new Date(p.startDate).toLocaleDateString()} - ${new Date(p.endDate).toLocaleDateString()}`}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Right Side: Selected Plan Details */}
        <Grid item xs={12} md={8}>
          {selectedPlan ? (
            <Card variant="outlined" sx={{ minHeight: 400 }}>
              <CardContent>
                <Typography variant="h5" fontWeight="bold" color="primary" gutterBottom>
                  {selectedPlan.title}
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  {selectedPlan.description || 'No description provided.'}
                </Typography>
                <Typography variant="caption" display="block" color="textSecondary" sx={{ mb: 3 }}>
                  Status: <strong>{selectedPlan.status}</strong>
                </Typography>

                <Typography variant="h6" display="flex" alignItems="center" gap={1} gutterBottom>
                  <CalendarToday /> Tasks Checklist
                </Typography>

                {selectedPlanItems.length === 0 ? (
                  <Typography variant="body2" color="textSecondary">No tasks created for this plan.</Typography>
                ) : (
                  <List>
                    {selectedPlanItems.map((item) => (
                      <ListItem key={item.id} sx={{ bgcolor: '#fdfdfd', border: '1px solid #eee', mb: 1, borderRadius: 1 }}>
                        <Checkbox
                          checked={item.status === 'COMPLETED'}
                          onChange={() => handleToggleItem(item.id, item.status)}
                          color="primary"
                        />
                        <ListItemText
                          primary={item.title}
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="textSecondary" display="block">
                                Scheduled: {new Date(item.scheduledDate).toLocaleDateString()} ({item.estimatedMinutes} mins)
                              </Typography>
                              {item.completedAt && (
                                <Typography component="span" variant="caption" color="success.main" display="block">
                                  ✓ Completed on {new Date(item.completedAt).toLocaleString()}
                                </Typography>
                              )}
                            </>
                          }
                          sx={{ textDecoration: item.status === 'COMPLETED' ? 'line-through' : 'none' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }} variant="outlined">
              <Typography color="textSecondary">Select a plan from the left panel to review or complete study tasks.</Typography>
            </Paper>
          )}
        </Grid>
      </Grid>

      {/* Create Dialog */}
      <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Custom Study Plan</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField
              label="Plan Title"
              fullWidth
              value={newPlan.title}
              onChange={(e) => setNewPlan({ ...newPlan, title: e.target.value })}
            />
            <TextField
              label="Plan Description"
              fullWidth
              multiline
              rows={3}
              value={newPlan.description}
              onChange={(e) => setNewPlan({ ...newPlan, description: e.target.value })}
            />
            <Stack direction="row" spacing={2}>
              <TextField
                label="Start Date"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={newPlan.startDate}
                onChange={(e) => setNewPlan({ ...newPlan, startDate: e.target.value })}
              />
              <TextField
                label="End Date"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={newPlan.endDate}
                onChange={(e) => setNewPlan({ ...newPlan, endDate: e.target.value })}
              />
            </Stack>
            <Typography variant="subtitle2" mt={1}>Initial Study Task</Typography>
            <TextField
              label="Task Name"
              fullWidth
              value={newPlan.taskTitle}
              onChange={(e) => setNewPlan({ ...newPlan, taskTitle: e.target.value })}
            />
            <TextField
              label="Estimated Duration (minutes)"
              type="number"
              fullWidth
              value={newPlan.taskMinutes}
              onChange={(e) => setNewPlan({ ...newPlan, taskMinutes: Number(e.target.value) })}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreate(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreatePlan}>Create Plan</Button>
        </DialogActions>
      </Dialog>

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default StudyPlanner;
