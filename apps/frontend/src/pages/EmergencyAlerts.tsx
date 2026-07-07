import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Grid,
  Select, MenuItem, InputLabel, FormControl, Alert, Divider, Table, TableBody, TableCell, TableHead, TableRow
} from '@mui/material';

export const EmergencyAlerts: React.FC = () => {
  const [activeAlerts, setActiveAlerts] = useState<any[]>([]);
  const [title, setTitle] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [severity, setSeverity] = useState<string>('HIGH');
  const [targetAudience, setTargetAudience] = useState<string>('ALL');
  const [locationText, setLocationText] = useState<string>('');
  const [instructions, setInstructions] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [error, setError] = useState<string>('');

  const fetchActiveAlerts = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/v1/notifications/emergency-alerts', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setActiveAlerts(payload.data.alerts || []);
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  useEffect(() => {
    fetchActiveAlerts();
  }, []);

  const handleTrigger = async () => {
    setError('');
    setSuccess('');

    if (!title || !message) {
      setError('Title and Message body are required.');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const payload = { title, message, severity, targetAudience, locationText, instructions };
      const res = await fetch('/api/v1/notifications/emergency-alerts', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSuccess('EMERGENCY ALERT TRIGGERED SYSTEM WIDE.');
        setTitle('');
        setMessage('');
        setLocationText('');
        setInstructions('');
        fetchActiveAlerts();
      } else {
        setError('Failed to trigger emergency alert.');
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  const handleResolve = async (id: string) => {
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/notifications/emergency-alerts/${id}/resolve`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setSuccess('Emergency alert resolved successfully.');
        fetchActiveAlerts();
      } else {
        setError('Failed to resolve alert.');
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'Outfit', mb: 4, color: 'error.main' }}>
        Emergency Broadcaster
      </Typography>

      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={4}>
        <Grid item xs={12} md={5}>
          <Card sx={{ border: '2px solid red', borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} color="error" gutterBottom>Trigger Emergency Broadcast</Typography>
              <Divider sx={{ mb: 3 }} />

              <TextField
                label="Alert Heading / Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
              />

              <TextField
                label="Incident Details / Message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                multiline
                rows={3}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
              />

              <TextField
                label="Location (Optional)"
                value={locationText}
                onChange={(e) => setLocationText(e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
                helperText="e.g. Block C, Science Wing"
              />

              <TextField
                label="Action Instructions (Optional)"
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                multiline
                rows={2}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
                helperText="e.g. Please evacuate immediately to the sports ground."
              />

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>Severity Level</InputLabel>
                <Select value={severity} label="Severity Level" onChange={(e) => setSeverity(e.target.value)}>
                  <MenuItem value="MEDIUM">Medium Alert</MenuItem>
                  <MenuItem value="HIGH">High Alert</MenuItem>
                  <MenuItem value="CRITICAL">Critical Emergency</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>Target Audience</InputLabel>
                <Select value={targetAudience} label="Target Audience" onChange={(e) => setTargetAudience(e.target.value)}>
                  <MenuItem value="ALL">Everyone on Campus</MenuItem>
                  <MenuItem value="STAFF">Staff & Faculty Only</MenuItem>
                  <MenuItem value="STUDENTS">Students Only</MenuItem>
                </Select>
              </FormControl>

              <Button variant="contained" color="error" fullWidth size="large" onClick={handleTrigger}>
                Trigger Emergency Alert
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={7}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Active System Emergencies</Typography>
              <Divider sx={{ mb: 3 }} />

              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Alert Details</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Severity</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Location</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {activeAlerts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} align="center">No active emergencies. The campus is safe.</TableCell>
                    </TableRow>
                  ) : (
                    activeAlerts.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight={600} color="error">{a.title}</Typography>
                          <Typography variant="caption" color="text.secondary">{a.message}</Typography>
                        </TableCell>
                        <TableCell>{a.severity}</TableCell>
                        <TableCell>{a.locationText || 'N/A'}</TableCell>
                        <TableCell>
                          <Button size="small" variant="contained" color="success" onClick={() => handleResolve(a.id)}>
                            Resolve
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
export default EmergencyAlerts;
