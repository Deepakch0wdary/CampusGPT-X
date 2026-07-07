import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Card, CardContent, Typography, Grid, IconButton,
  Button, Select, MenuItem, InputLabel, FormControl, Pagination, Alert
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Drafts as ReadIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

export const NotificationCenter: React.FC = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [priority, setPriority] = useState<string>('');
  const [type, setType] = useState<string>('');
  const [channel, setChannel] = useState<string>('');
  const [unreadOnly, setUnreadOnly] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('access_token');
      let url = `/api/v1/notifications?page=${page}&size=10`;
      if (unreadOnly) url += '&unread_only=true';
      if (priority) url += `&priority=${priority}`;
      if (type) url += `&type=${type}`;
      if (channel) url += `&channel=${channel}`;

      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setNotifications(payload.data.notifications || []);
        setTotal(payload.data.total || 0);
      } else {
        setError('Failed to fetch notifications.');
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [page, priority, type, channel, unreadOnly]);

  const handleMarkRead = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`/api/v1/notifications/${id}/read`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchNotifications();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`/api/v1/notifications/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchNotifications();
    } catch (e) {
      console.error(e);
    }
  };

  const handleReadAll = async () => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch('/api/v1/notifications/read-all', {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchNotifications();
    } catch (e) {
      console.error(e);
    }
  };

  const getAlertSeverity = (type: string) => {
    switch (type.toUpperCase()) {
      case 'WARNING': return 'warning';
      case 'ERROR': return 'error';
      case 'EMERGENCY': return 'error';
      case 'SUCCESS': return 'success';
      default: return 'info';
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'Outfit' }}>
          Notification Center
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => navigate('/notification-preferences')}
          >
            Preferences
          </Button>
          {notifications.some(n => !n.readAt) && (
            <Button variant="contained" onClick={handleReadAll}>
              Mark All Read
            </Button>
          )}
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Card sx={{ mb: 4, border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Priority</InputLabel>
                <Select value={priority} label="Priority" onChange={(e) => { setPriority(e.target.value); setPage(1); }}>
                  <MenuItem value="">All Priorities</MenuItem>
                  <MenuItem value="LOW">Low</MenuItem>
                  <MenuItem value="MEDIUM">Medium</MenuItem>
                  <MenuItem value="HIGH">High</MenuItem>
                  <MenuItem value="CRITICAL">Critical</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Type</InputLabel>
                <Select value={type} label="Type" onChange={(e) => { setType(e.target.value); setPage(1); }}>
                  <MenuItem value="">All Types</MenuItem>
                  <MenuItem value="INFO">Info</MenuItem>
                  <MenuItem value="WARNING">Warning</MenuItem>
                  <MenuItem value="SUCCESS">Success</MenuItem>
                  <MenuItem value="ERROR">Error</MenuItem>
                  <MenuItem value="EMERGENCY">Emergency</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Channel</InputLabel>
                <Select value={channel} label="Channel" onChange={(e) => { setChannel(e.target.value); setPage(1); }}>
                  <MenuItem value="">All Channels</MenuItem>
                  <MenuItem value="IN_APP">In App</MenuItem>
                  <MenuItem value="EMAIL">Email</MenuItem>
                  <MenuItem value="SMS">SMS</MenuItem>
                  <MenuItem value="PUSH">Push</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button
                variant={unreadOnly ? "contained" : "outlined"}
                fullWidth
                size="medium"
                onClick={() => { setUnreadOnly(!unreadOnly); setPage(1); }}
              >
                {unreadOnly ? "Showing Unread" : "Show Unread Only"}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {notifications.length === 0 ? (
          <Grid item xs={12}>
            <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', py: 6, textAlign: 'center', borderRadius: 2 }}>
              <CardContent>
                <Typography color="text.secondary">No notifications found.</Typography>
              </CardContent>
            </Card>
          </Grid>
        ) : (
          notifications.map((n) => (
            <Grid item xs={12} key={n.id}>
              <Card
                sx={{
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  bgcolor: n.readAt ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 112, 243, 0.05)',
                  borderRadius: 2,
                  transition: 'transform 0.2s',
                  '&:hover': { transform: 'translateY(-2px)' }
                }}
              >
                <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Alert
                        severity={getAlertSeverity(n.type)}
                        icon={false}
                        sx={{ py: 0, px: 1, fontSize: 10, fontWeight: 700 }}
                      >
                        {n.priority}
                      </Alert>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(n.createdAt).toLocaleString()}
                      </Typography>
                    </Box>
                    <Typography variant="h6" fontWeight={n.readAt ? 500 : 700} sx={{ mb: 1 }}>
                      {n.title}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {n.body}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {!n.readAt && (
                      <IconButton color="primary" onClick={() => handleMarkRead(n.id)} title="Mark as Read">
                        <ReadIcon />
                      </IconButton>
                    )}
                    <IconButton color="error" onClick={() => handleDismiss(n.id)} title="Dismiss">
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {total > 10 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Pagination
            count={Math.ceil(total / 10)}
            page={page}
            onChange={(_, p) => setPage(p)}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
};
export default NotificationCenter;
