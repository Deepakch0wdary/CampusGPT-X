import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Grid,
  Select, MenuItem, InputLabel, FormControl, Alert, Divider, Table, TableBody, TableCell, TableHead, TableRow
} from '@mui/material';

export const AnnouncementManager: React.FC = () => {
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [title, setTitle] = useState<string>('');
  const [body, setBody] = useState<string>('');
  const [audienceType, setAudienceType] = useState<string>('ALL');
  const [priority, setPriority] = useState<string>('LOW');
  const status = 'PUBLISHED';
  const pinned = false;
  const [success, setSuccess] = useState<string>('');
  const [error, setError] = useState<string>('');

  const fetchAnnouncements = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/v1/notifications/announcements', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setAnnouncements(payload.data.announcements || []);
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  const handleCreate = async () => {
    setError('');
    setSuccess('');

    if (!title || !body) {
      setError('Title and Body are required fields.');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const payload = { title, body, audienceType, priority, status, pinned };
      const res = await fetch('/api/v1/notifications/announcements', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSuccess('Announcement published successfully.');
        setTitle('');
        setBody('');
        fetchAnnouncements();
      } else {
        setError('Failed to create announcement.');
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'Outfit', mb: 4 }}>
        Announcement Manager
      </Typography>

      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={4}>
        <Grid item xs={12} md={5}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Create Announcement</Typography>
              <Divider sx={{ mb: 3 }} />

              <TextField
                label="Notice Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
              />

              <TextField
                label="Content / Body"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                multiline
                rows={4}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
              />

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>Target Audience</InputLabel>
                <Select value={audienceType} label="Target Audience" onChange={(e) => setAudienceType(e.target.value)}>
                  <MenuItem value="ALL">All Campus (Everyone)</MenuItem>
                  <MenuItem value="ROLE">Specific Role</MenuItem>
                  <MenuItem value="DEPARTMENT">Specific Department</MenuItem>
                  <MenuItem value="SECTION">Specific Section</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>Priority</InputLabel>
                <Select value={priority} label="Priority" onChange={(e) => setPriority(e.target.value)}>
                  <MenuItem value="LOW">Low</MenuItem>
                  <MenuItem value="MEDIUM">Medium</MenuItem>
                  <MenuItem value="HIGH">High</MenuItem>
                  <MenuItem value="EMERGENCY">Emergency</MenuItem>
                </Select>
              </FormControl>

              <Button variant="contained" fullWidth size="large" onClick={handleCreate}>
                Publish Notice
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={7}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Active Announcements</Typography>
              <Divider sx={{ mb: 3 }} />

              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Title</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Audience</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Priority</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {announcements.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} align="center">No active announcements</TableCell>
                    </TableRow>
                  ) : (
                    announcements.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell>{a.title}</TableCell>
                        <TableCell>{a.audienceType}</TableCell>
                        <TableCell>{a.priority}</TableCell>
                        <TableCell>{new Date(a.publishAt).toLocaleDateString()}</TableCell>
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
export default AnnouncementManager;
