import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, Button, TextField, LinearProgress, Stack, Dialog, DialogTitle, DialogContent, DialogActions, Select, MenuItem, InputLabel, FormControl, Alert, IconButton, Chip
} from '@mui/material';
import { Add, Delete, Flag } from '@mui/icons-material';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const StudentGoals: React.FC = () => {
  const [goals, setGoals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  // Dialogs
  const [openCreate, setOpenCreate] = useState(false);
  const [newGoal, setNewGoal] = useState({
    title: '',
    targetType: 'MARKS',
    targetValue: 80,
    deadline: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  });

  const [openUpdate, setOpenUpdate] = useState(false);
  const [updatingGoalId, setUpdatingGoalId] = useState<string | null>(null);
  const [updateForm, setUpdateForm] = useState({
    currentValue: 0,
    status: 'ACTIVE'
  });

  const fetchGoals = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/me/goals', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success) {
          setGoals(payload.data || []);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGoal = async () => {
    const token = localStorage.getItem('access_token');
    const payload = {
      title: newGoal.title,
      targetType: newGoal.targetType,
      targetValue: Number(newGoal.targetValue),
      deadline: new Date(newGoal.deadline).toISOString()
    };
    try {
      const res = await fetch('/api/v1/academic-mentor/me/goals', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setAlert({ type: 'success', msg: "New academic goal set successfully." });
        setOpenCreate(false);
        fetchGoals();
      } else {
        const errPayload = await res.json();
        setAlert({ type: 'error', msg: errPayload.message || "Failed to create goal." });
      }
    } catch (e) {
      setAlert({ type: 'error', msg: "Network error occurred." });
    }
  };

  const handleUpdateGoal = async () => {
    if (!updatingGoalId) return;
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/academic-mentor/me/goals/${updatingGoalId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          currentValue: Number(updateForm.currentValue),
          status: updateForm.status
        })
      });
      if (res.ok) {
        setAlert({ type: 'success', msg: "Goal status updated." });
        setOpenUpdate(false);
        fetchGoals();
      } else {
        const errPayload = await res.json();
        setAlert({ type: 'error', msg: errPayload.message || "Failed to update goal." });
      }
    } catch (e) {
      setAlert({ type: 'error', msg: "Network error occurred." });
    }
  };

  const handleDeleteGoal = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this goal?")) return;
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/academic-mentor/me/goals/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setAlert({ type: 'success', msg: "Goal deleted successfully." });
        fetchGoals();
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchGoals();
  }, []);

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography mt={2}>Loading Academic Goals...</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2} mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary">My Academic Goals</Typography>
          <Typography variant="subtitle1" color="textSecondary">Configure benchmarks to guide your academic revision schedule.</Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setOpenCreate(true)}>
          Set New Goal
        </Button>
      </Box>

      {alert && <Alert severity={alert.type} sx={{ mb: 3 }} onClose={() => setAlert(null)}>{alert.msg}</Alert>}

      {goals.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">You have not defined any goals yet. Click 'Set New Goal' to get started!</Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {goals.map((g) => {
            const progressPct = g.targetValue > 0 ? Math.min((g.currentValue || 0) / g.targetValue * 100, 100) : 0;
            return (
              <Grid item xs={12} md={6} key={g.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="start">
                      <Box display="flex" gap={1.5} alignItems="center">
                        <Flag color={g.status === 'COMPLETED' ? 'success' : 'primary'} />
                        <Typography variant="h6" fontWeight="600">{g.title}</Typography>
                      </Box>
                      <IconButton size="small" onClick={() => handleDeleteGoal(g.id)} color="error">
                        <Delete />
                      </IconButton>
                    </Box>

                    <Box mt={2}>
                      <Typography variant="body2" color="textSecondary">
                        Target Type: <strong>{g.targetType}</strong>
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Target: <strong>{g.targetValue}</strong> | Current: <strong>{g.currentValue || 0}</strong>
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Deadline: {g.deadline ? new Date(g.deadline).toLocaleDateString() : 'None'}
                      </Typography>
                    </Box>

                    <Box mt={3}>
                      <Box display="flex" justifyContent="space-between" mb={0.5}>
                        <Typography variant="caption" color="textSecondary">Goal Progress</Typography>
                        <Typography variant="caption" fontWeight="bold">{Math.round(progressPct)}%</Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={progressPct}
                        color={g.status === 'COMPLETED' ? 'success' : 'primary'}
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                    </Box>

                    <Box mt={2} display="flex" justifyContent="space-between" alignItems="center">
                      <Chip label={g.status} color={g.status === 'COMPLETED' ? 'success' : 'primary'} size="small" />
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          setUpdatingGoalId(g.id);
                          setUpdateForm({ currentValue: g.currentValue || 0, status: g.status });
                          setOpenUpdate(true);
                        }}
                      >
                        Update Progress
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Create Goal Dialog */}
      <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Set New Academic Goal</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField
              label="Goal Title"
              fullWidth
              value={newGoal.title}
              onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Target Metric</InputLabel>
              <Select
                value={newGoal.targetType}
                label="Target Metric"
                onChange={(e) => setNewGoal({ ...newGoal, targetType: e.target.value })}
              >
                <MenuItem value="MARKS">Marks Percentage (%)</MenuItem>
                <MenuItem value="ATTENDANCE">Attendance Rate (%)</MenuItem>
                <MenuItem value="STUDY_MINUTES">Study Session Minutes</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Target Value"
              type="number"
              fullWidth
              value={newGoal.targetValue}
              onChange={(e) => setNewGoal({ ...newGoal, targetValue: Number(e.target.value) })}
            />
            <TextField
              label="Target Deadline"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newGoal.deadline}
              onChange={(e) => setNewGoal({ ...newGoal, deadline: e.target.value })}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreate(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateGoal}>Set Goal</Button>
        </DialogActions>
      </Dialog>

      {/* Update Progress Dialog */}
      <Dialog open={openUpdate} onClose={() => setOpenUpdate(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Update Goal Progress</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField
              label="Current Value"
              type="number"
              fullWidth
              value={updateForm.currentValue}
              onChange={(e) => setUpdateForm({ ...updateForm, currentValue: Number(e.target.value) })}
            />
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={updateForm.status}
                label="Status"
                onChange={(e) => setUpdateForm({ ...updateForm, status: e.target.value })}
              >
                <MenuItem value="ACTIVE">ACTIVE</MenuItem>
                <MenuItem value="COMPLETED">COMPLETED</MenuItem>
                <MenuItem value="ABANDONED">ABANDONED</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenUpdate(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateGoal}>Update</Button>
        </DialogActions>
      </Dialog>

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default StudentGoals;
