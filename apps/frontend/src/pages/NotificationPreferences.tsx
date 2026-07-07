import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Grid, FormControlLabel, Switch,
  Button, TextField, Select, MenuItem, InputLabel, FormControl, Alert, Divider
} from '@mui/material';

export const NotificationPreferences: React.FC = () => {
  const [preferences, setPreferences] = useState<any>(null);
  const [quietHoursEnabled, setQuietHoursEnabled] = useState<boolean>(false);
  const [quietHoursStart, setQuietHoursStart] = useState<string>('22:00');
  const [quietHoursEnd, setQuietHoursEnd] = useState<string>('07:00');
  const [timezone, setTimezone] = useState<string>('UTC');
  const [success, setSuccess] = useState<string>('');
  const [error, setError] = useState<string>('');

  const fetchPrefs = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/v1/notifications/preferences', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        const data = payload.data;
        setPreferences(data);
        setQuietHoursEnabled(data.quietHoursEnabled);
        setQuietHoursStart(data.quietHoursStart || '22:00');
        setQuietHoursEnd(data.quietHoursEnd || '07:00');
        setTimezone(data.timezone || 'UTC');
      }
    } catch (e) {
      setError('Failed to fetch preferences.');
    }
  };

  useEffect(() => {
    fetchPrefs();
  }, []);

  const handleToggle = (key: string) => {
    if (!preferences) return;
    setPreferences({
      ...preferences,
      [key]: !preferences[key]
    });
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');

    // Time validation HH:MM
    const timeRegex = /^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$/;
    if (quietHoursEnabled) {
      if (!timeRegex.test(quietHoursStart) || !timeRegex.test(quietHoursEnd)) {
        setError('Quiet Hours start and end times must be in HH:MM (24-hour) format.');
        return;
      }
    }

    try {
      const token = localStorage.getItem('access_token');
      const payload = {
        ...preferences,
        quietHoursEnabled,
        quietHoursStart,
        quietHoursEnd,
        timezone
      };

      const res = await fetch('/api/v1/notifications/preferences', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSuccess('Preferences updated successfully.');
        fetchPrefs();
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Failed to update preferences.');
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  if (!preferences) {
    return <Typography sx={{ p: 4 }}>Loading preferences...</Typography>;
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'Outfit', mb: 4 }}>
        Notification Preferences
      </Typography>

      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={4}>
        <Grid item xs={12} md={6}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Delivery Channels</Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={<Switch checked={preferences.inAppEnabled} onChange={() => handleToggle('inAppEnabled')} />}
                    label="In-App (Portal Bell Alert)"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={<Switch checked={preferences.emailEnabled} onChange={() => handleToggle('emailEnabled')} />}
                    label="Email Notifications"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={<Switch checked={preferences.smsEnabled} onChange={() => handleToggle('smsEnabled')} />}
                    label="SMS Alerts"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={<Switch checked={preferences.pushEnabled} onChange={() => handleToggle('pushEnabled')} />}
                    label="Mobile Push Notifications"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2, mt: 4 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Notification Categories</Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <FormControlLabel
                    control={<Switch checked={preferences.academicEnabled} onChange={() => handleToggle('academicEnabled')} />}
                    label="Academics"
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControlLabel
                    control={<Switch checked={preferences.attendanceEnabled} onChange={() => handleToggle('attendanceEnabled')} />}
                    label="Attendance Alerts"
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControlLabel
                    control={<Switch checked={preferences.feeEnabled} onChange={() => handleToggle('feeEnabled')} />}
                    label="Fee Reminders"
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControlLabel
                    control={<Switch checked={preferences.examEnabled} onChange={() => handleToggle('examEnabled')} />}
                    label="Exam Updates"
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControlLabel
                    control={<Switch checked={preferences.resultEnabled} onChange={() => handleToggle('resultEnabled')} />}
                    label="Results"
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControlLabel
                    control={<Switch checked={preferences.transportEnabled} onChange={() => handleToggle('transportEnabled')} />}
                    label="Transit Alerts"
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControlLabel
                    control={<Switch checked={preferences.hostelEnabled} onChange={() => handleToggle('hostelEnabled')} />}
                    label="Hostel Updates"
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControlLabel
                    control={<Switch checked={preferences.libraryEnabled} onChange={() => handleToggle('libraryEnabled')} />}
                    label="Library Notices"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Quiet Hours & Timezone</Typography>
              <Divider sx={{ mb: 3 }} />

              <Box sx={{ mb: 4 }}>
                <FormControlLabel
                  control={<Switch checked={quietHoursEnabled} onChange={(e) => setQuietHoursEnabled(e.target.checked)} />}
                  label="Enable Quiet Hours (DND Mode)"
                />
              </Box>

              {quietHoursEnabled && (
                <Grid container spacing={2} sx={{ mb: 4 }}>
                  <Grid item xs={6}>
                    <TextField
                      label="Quiet Hours Start"
                      type="text"
                      value={quietHoursStart}
                      onChange={(e) => setQuietHoursStart(e.target.value)}
                      fullWidth
                      helperText="24-hour format HH:MM (e.g. 22:00)"
                      size="small"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      label="Quiet Hours End"
                      type="text"
                      value={quietHoursEnd}
                      onChange={(e) => setQuietHoursEnd(e.target.value)}
                      fullWidth
                      helperText="24-hour format HH:MM (e.g. 07:00)"
                      size="small"
                    />
                  </Grid>
                </Grid>
              )}

              <FormControl fullWidth size="small" sx={{ mb: 4 }}>
                <InputLabel>Timezone</InputLabel>
                <Select value={timezone} label="Timezone" onChange={(e) => setTimezone(e.target.value)}>
                  <MenuItem value="UTC">UTC</MenuItem>
                  <MenuItem value="Asia/Kolkata">Asia/Kolkata</MenuItem>
                  <MenuItem value="America/New_York">America/New_York</MenuItem>
                  <MenuItem value="Europe/London">Europe/London</MenuItem>
                </Select>
              </FormControl>

              <Button variant="contained" fullWidth size="large" onClick={handleSave}>
                Save Preferences
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
export default NotificationPreferences;
