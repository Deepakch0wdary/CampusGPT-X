import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Grid,
  Select, MenuItem, InputLabel, FormControl, Alert, Divider, Table, TableBody, TableCell, TableHead, TableRow
} from '@mui/material';

export const BroadcastManager: React.FC = () => {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [name, setName] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [body, setBody] = useState<string>('');
  const [audienceType, setAudienceType] = useState<string>('ALL');
  const [success, setSuccess] = useState<string>('');
  const [error, setError] = useState<string>('');

  const fetchCampaigns = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/v1/notifications/campaigns', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setCampaigns(payload.data.campaigns || []);
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const handleCreate = async () => {
    setError('');
    setSuccess('');

    if (!name || !title || !body) {
      setError('Campaign name, title, and body are required fields.');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const payload = { name, title, body, audienceType };
      const res = await fetch('/api/v1/notifications/campaigns', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSuccess('Campaign draft created successfully.');
        setName('');
        setTitle('');
        setBody('');
        fetchCampaigns();
      } else {
        setError('Failed to create campaign draft.');
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  const handleSend = async (id: string) => {
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/v1/notifications/campaigns/${id}/send`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setSuccess('Campaign triggered successfully.');
        fetchCampaigns();
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to dispatch campaign.');
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'Outfit', mb: 4 }}>
        Broadcast Campaigns
      </Typography>

      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={4}>
        <Grid item xs={12} md={5}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Create Campaign Draft</Typography>
              <Divider sx={{ mb: 3 }} />

              <TextField
                label="Campaign Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
                helperText="Internal identifier (e.g. Autumn Semester Welcome)"
              />

              <TextField
                label="Message Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
                helperText="Subject line visible to recipients"
              />

              <TextField
                label="Message Body / Content"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                multiline
                rows={4}
                fullWidth
                size="small"
                sx={{ mb: 3 }}
              />

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>Recipient Group</InputLabel>
                <Select value={audienceType} label="Recipient Group" onChange={(e) => setAudienceType(e.target.value)}>
                  <MenuItem value="ALL">All Portal Users</MenuItem>
                  <MenuItem value="ROLE">Filter by User Role</MenuItem>
                  <MenuItem value="DEPARTMENT">Filter by Department</MenuItem>
                </Select>
              </FormControl>

              <Button variant="contained" fullWidth size="large" onClick={handleCreate}>
                Save Campaign Draft
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={7}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>All Broadcast Campaigns</Typography>
              <Divider sx={{ mb: 3 }} />

              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Campaign</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Audience</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Success / Total</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {campaigns.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} align="center">No campaigns found</TableCell>
                    </TableRow>
                  ) : (
                    campaigns.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight={600}>{c.name}</Typography>
                          <Typography variant="caption" color="text.secondary">{c.title}</Typography>
                        </TableCell>
                        <TableCell>
                          <Alert
                            severity={c.status === 'COMPLETED' ? 'success' : c.status === 'DRAFT' ? 'info' : 'warning'}
                            icon={false}
                            sx={{ py: 0, px: 1, fontSize: 10, display: 'inline-flex' }}
                          >
                            {c.status}
                          </Alert>
                        </TableCell>
                        <TableCell>{c.audienceType}</TableCell>
                        <TableCell>{c.successCount} / {c.totalRecipients}</TableCell>
                        <TableCell>
                          {c.status === 'DRAFT' && (
                            <Button size="small" variant="contained" onClick={() => handleSend(c.id)}>
                              Send
                            </Button>
                          )}
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
export default BroadcastManager;
