import React, { useState } from 'react';
import {
  Box, Typography, Paper, TextField, Button, MenuItem, Select, FormControl, InputLabel, Stack, Dialog, DialogTitle, DialogContent, DialogActions, Alert
} from '@mui/material';
import { Add } from '@mui/icons-material';
import { useLocation } from 'react-router-dom';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const InterventionManager: React.FC = () => {
  const location = useLocation();
  const initStudentId = location.state?.studentId || '';
  const initStudentName = location.state?.studentName || '';

  const [studentId, setStudentId] = useState(initStudentId);
  const [studentName] = useState(initStudentName);

  const [open, setOpen] = useState(!!initStudentId);
  const [form, setForm] = useState({
    type: 'TUTORING',
    reason: '',
    notes: '',
    dueAt: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  });

  const [alert, setAlert] = useState<{ type: 'success' | 'error', msg: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!studentId) {
      setAlert({ type: 'error', msg: "No student ID selected for intervention." });
      return;
    }
    setLoading(true);
    const token = localStorage.getItem('access_token');
    const payload = {
      type: form.type,
      reason: form.reason,
      notes: form.notes,
      dueAt: new Date(form.dueAt).toISOString()
    };

    try {
      const res = await fetch(`/api/v1/academic-mentor/students/${studentId}/interventions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setAlert({ type: 'success', msg: `Academic support intervention registered for student ${studentName || studentId}.` });
        setOpen(false);
      } else {
        const errPayload = await res.json();
        setAlert({ type: 'error', msg: errPayload.message || "Failed to create intervention." });
      }
    } catch (e) {
      setAlert({ type: 'error', msg: "Network error occurred." });
    } finally {
      setLoading(false);
    }
  };



  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary">Mentor Intervention Workflow</Typography>
          <Typography variant="subtitle1" color="textSecondary">Initiate formal academic support, remedial sessions, or check-ins.</Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setOpen(true)}>
          New Intervention
        </Button>
      </Box>

      {alert && <Alert severity={alert.type} sx={{ mb: 3 }} onClose={() => setAlert(null)}>{alert.msg}</Alert>}

      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography color="textSecondary" gutterBottom>
          Select a student from the Teacher Directory to initialize an intervention plan, or click "New Intervention" to assign a plan.
        </Typography>
      </Paper>

      {/* Intervention Dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Initiate Academic Support Intervention</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField
              label="Student ID"
              fullWidth
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              disabled={!!initStudentId}
            />
            {studentName && (
              <Typography variant="body2" color="textSecondary">
                Student Name: <strong>{studentName}</strong>
              </Typography>
            )}
            <FormControl fullWidth>
              <InputLabel>Support Type</InputLabel>
              <Select
                value={form.type}
                label="Support Type"
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                <MenuItem value="TUTORING">Peer/Faculty Tutoring</MenuItem>
                <MenuItem value="ACADEMIC_PROBATION">Academic Probation Review</MenuItem>
                <MenuItem value="ATTENDANCE_REVIEW">Attendance Deficit Review</MenuItem>
                <MenuItem value="COUNSELING">Support Counseling Session</MenuItem>
                <MenuItem value="EXAM_PREP_PLAN">Exam Preparation Outline</MenuItem>
                <MenuItem value="OTHER">Other Custom Intervention</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Initiation Reason"
              fullWidth
              multiline
              rows={2}
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
            />
            <TextField
              label="Private Mentoring Notes"
              fullWidth
              multiline
              rows={3}
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
            <TextField
              label="Due Date / Resolution Deadline"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={form.dueAt}
              onChange={(e) => setForm({ ...form, dueAt: e.target.value })}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSubmit} disabled={loading}>
            {loading ? 'Submitting...' : 'Register Intervention'}
          </Button>
        </DialogActions>
      </Dialog>

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default InterventionManager;
