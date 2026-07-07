import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Card, CardContent, Typography, Grid, Divider, Alert
} from '@mui/material';
import {
  Campaign as CampaignIcon,
  Warning as EmergencyIcon,
  SettingsSuggest as TemplateIcon,
  Announcement as AnnouncementIcon,
  SimCard as SimulatorIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';

export const CommunicationDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/v1/notifications/analytics', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setAnalytics(payload.data);
      } else {
        setError('Failed to fetch analytics.');
      }
    } catch (e) {
      setError('Connection error.');
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4, alignItems: 'center' }}>
        <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'Outfit' }}>
          Communication Management
        </Typography>
        <Alert severity="info" icon={<SimulatorIcon />} sx={{ py: 0.5, borderRadius: 2 }}>
          Provider Mode: SIMULATED (Demo Sandbox)
        </Alert>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Grid container spacing={4} sx={{ mb: 6 }}>
        <Grid item xs={12} sm={6} md={3} onClick={() => navigate('/announcements')} sx={{ cursor: 'pointer' }}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2, '&:hover': { bgcolor: 'rgba(255,255,255,0.03)' } }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <AnnouncementIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Announcements</Typography>
                <Typography variant="h6" fontWeight={700}>Manage Notices</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3} onClick={() => navigate('/broadcasts')} sx={{ cursor: 'pointer' }}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2, '&:hover': { bgcolor: 'rgba(255,255,255,0.03)' } }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CampaignIcon color="secondary" fontSize="large" />
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Campaigns</Typography>
                <Typography variant="h6" fontWeight={700}>Bulk Broadcasts</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3} onClick={() => navigate('/emergency-alerts')} sx={{ cursor: 'pointer' }}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2, '&:hover': { bgcolor: 'rgba(255,255,255,0.03)' } }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <EmergencyIcon color="error" fontSize="large" />
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Emergency</Typography>
                <Typography variant="h6" fontWeight={700}>Critical Triggers</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3} onClick={() => navigate('/notification-templates')} sx={{ cursor: 'pointer' }}>
          <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2, '&:hover': { bgcolor: 'rgba(255,255,255,0.03)' } }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <TemplateIcon color="success" fontSize="large" />
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Templates</Typography>
                <Typography variant="h6" fontWeight={700}>Manage Templates</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {analytics && (
        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2, height: '100%' }}>
              <CardContent>
                <Typography variant="h6" fontWeight={700} gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AnalyticsIcon /> Delivery Metrics
                </Typography>
                <Divider sx={{ mb: 3 }} />
                <Grid container spacing={3}>
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'rgba(0, 112, 243, 0.05)', borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={800} color="primary.main">{analytics.totalNotifications}</Typography>
                      <Typography variant="body2" color="text.secondary">Total Sent</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'rgba(225, 29, 72, 0.05)', borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={800} color="error.main">{analytics.activeEmergencyAlerts}</Typography>
                      <Typography variant="body2" color="text.secondary">Active Emergencies</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'rgba(16, 185, 129, 0.05)', borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h5" fontWeight={700} color="success.main">{analytics.deliveryStats.delivered}</Typography>
                      <Typography variant="body2" color="text.secondary">Delivered Successfully</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'rgba(239, 68, 68, 0.05)', borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h5" fontWeight={700} color="error.main">{analytics.deliveryStats.failed}</Typography>
                      <Typography variant="body2" color="text.secondary">Failed / Suppressed</Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 2, height: '100%' }}>
              <CardContent>
                <Typography variant="h6" fontWeight={700} gutterBottom>Channel Distribution</Typography>
                <Divider sx={{ mb: 3 }} />
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">In-App Notifications</Typography>
                    <Typography variant="h5" fontWeight={700} sx={{ mb: 2 }}>{analytics.channelDistribution.inApp}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">Email Notifications</Typography>
                    <Typography variant="h5" fontWeight={700} sx={{ mb: 2 }}>{analytics.channelDistribution.email}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">SMS Delivery Logs</Typography>
                    <Typography variant="h5" fontWeight={700} sx={{ mb: 2 }}>{analytics.channelDistribution.sms}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">Push Notifications</Typography>
                    <Typography variant="h5" fontWeight={700} sx={{ mb: 2 }}>{analytics.channelDistribution.push}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};
export default CommunicationDashboard;
