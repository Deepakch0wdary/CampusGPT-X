import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Grid,
  Select, MenuItem, InputLabel, FormControl, Alert, Divider, Table, TableBody, TableCell, TableHead, TableRow
} from '@mui/material';

export const NotificationTemplates: React.FC = () => {
  const [templates, setTemplates] = useState<any[]>([]);
  const [name, setName] = useState<string>('');
  const [code, setCode] = useState<string>('');
  const [subjectTemplate, setSubjectTemplate] = useState<string>('');
  const [bodyTemplate, setBodyTemplate] = useState<string>('');
  const [channel, setChannel] = useState<string>('EMAIL');
  const [category, setCategory] = useState<string>('ACADEMIC');
  const [success, setSuccess] = useState<string>('');
  const [error, setError] = useState<string>('');

  const fetchTemplates = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/v1/notifications/templates', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setTemplates(payload.data.templates || []);
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleCreate = async () => {
    setError('');
    setSuccess('');

    if (!name || !code || !subjectTemplate || !bodyTemplate) {
      setError('All fields are required.');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const payload = { name, code, subjectTemplate, bodyTemplate, channel, category };
      const res = await fetch('/api/v1/notifications/templates', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSuccess('Template created successfully.');
        setName('');
        setCode('');
        setSubjectTemplate('');
        setBodyTemplate('');
        fetchTemplates();
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to create template.');
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'Outfit', mb: 4 }}>
        Notification Templates
      </Typography>

      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={4}>
        <Grid item xs={12} md={5}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Create Notification Template</Typography>
              <Divider sx={{ mb: 3 }} />

              <TextField
                label="Template Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
                helperText="e.g. Attendance Warning Email"
              />

              <TextField
                label="Template Code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
                helperText="Unique system slug: e.g. ATTENDANCE_WARN"
              />

              <TextField
                label="Subject Template"
                value={subjectTemplate}
                onChange={(e) => setSubjectTemplate(e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
                helperText="Supports variables e.g. Attendance Shortage for {{ studentName }}"
              />

              <TextField
                label="Body Template"
                value={bodyTemplate}
                onChange={(e) => setBodyTemplate(e.target.value)}
                multiline
                rows={4}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
                helperText="HTML or plain text template body"
              />

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>Channel</InputLabel>
                <Select value={channel} label="Channel" onChange={(e) => setChannel(e.target.value)}>
                  <MenuItem value="EMAIL">Email</MenuItem>
                  <MenuItem value="SMS">SMS</MenuItem>
                  <MenuItem value="PUSH">Mobile Push</MenuItem>
                  <MenuItem value="IN_APP">In Portal Bell</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>Category</InputLabel>
                <Select value={category} label="Category" onChange={(e) => setCategory(e.target.value)}>
                  <MenuItem value="ACADEMIC">Academics</MenuItem>
                  <MenuItem value="ATTENDANCE">Attendance</MenuItem>
                  <MenuItem value="FEES">Fees</MenuItem>
                  <MenuItem value="EXAMS">Exams</MenuItem>
                  <MenuItem value="RESULTS">Results</MenuItem>
                  <MenuItem value="EMERGENCY">Emergency</MenuItem>
                  <MenuItem value="GENERAL">General Notifications</MenuItem>
                </Select>
              </FormControl>

              <Button variant="contained" fullWidth size="large" onClick={handleCreate}>
                Save Template
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={7}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Template Registry</Typography>
              <Divider sx={{ mb: 3 }} />

              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Code / Name</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Channel</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Active</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {templates.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} align="center">No templates registered</TableCell>
                    </TableRow>
                  ) : (
                    templates.map((t) => (
                      <TableRow key={t.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight={600}>{t.code}</Typography>
                          <Typography variant="caption" color="text.secondary">{t.name}</Typography>
                        </TableCell>
                        <TableCell>{t.channel}</TableCell>
                        <TableCell>{t.category}</TableCell>
                        <TableCell>{t.active ? 'Yes' : 'No'}</TableCell>
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
export default NotificationTemplates;
