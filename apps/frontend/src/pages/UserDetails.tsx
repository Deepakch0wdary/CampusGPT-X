import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Typography, 
  Paper, 
  Box, 
  CircularProgress, 
  Alert, 
  Button, 
  Grid,
  Divider,
  Chip
} from '@mui/material';
import { ArrowBack as BackIcon, AccountBox as UserIcon } from '@mui/icons-material';

interface UserDetail {
  id: string;
  name: string;
  email: string;
  username: string;
  role: string;
  status: string;
  department: string | null;
  section: string | null;
  createdAt: string;
  profile: {
    phoneNumber: string | null;
    bio: string | null;
    address: string | null;
    avatarUrl: string | null;
    designation: string | null;
  };
  permissions: string[];
}

export const UserDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [userDetail, setUserDetail] = useState<UserDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUserDetails = async () => {
    setLoading(true);
    setError(null);
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await fetch(`/api/v1/users/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to fetch user profiles.');
      }

      setUserDetail(data.user);
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserDetails();
  }, [id]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 128px)' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !userDetail) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">{error || 'Failed to load user details.'}</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/dashboard')} sx={{ mt: 2 }}>
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Button startIcon={<BackIcon />} onClick={() => navigate('/dashboard')} sx={{ mb: 4 }}>
        Back to Directory
      </Button>

      <Grid container spacing={4}>
        {/* Profile Card */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 4, textCenter: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: 'background.paper' }}>
            <UserIcon sx={{ fontSize: 96, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 0.5, fontFamily: 'Outfit' }}>{userDetail.name}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>@{userDetail.username}</Typography>
            
            <Chip 
              label={userDetail.role} 
              color={userDetail.role === 'MASTER_ADMIN' ? 'secondary' : 'default'} 
              sx={{ mb: 1 }} 
            />
            <Chip 
              label={userDetail.status} 
              color={userDetail.status === 'ACTIVE' ? 'success' : 'error'} 
              variant="outlined" 
            />
          </Paper>
        </Grid>

        {/* Configurations Details */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
            <Typography variant="h5" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 3 }}>
              Academic & Profile Diagnostics
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">Email Address</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500, mb: 2 }}>{userDetail.email}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">Contact Phone</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500, mb: 2 }}>{userDetail.profile.phoneNumber || 'Not configured'}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">Department Mapped</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500, mb: 2 }}>{userDetail.department || 'None'}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">Section Mapped</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500, mb: 2 }}>{userDetail.section || 'None'}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">Staff Designation</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500, mb: 2 }}>{userDetail.profile.designation || 'None'}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">Provisioning Date</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500, mb: 2 }}>{new Date(userDetail.createdAt).toLocaleString()}</Typography>
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            <Typography variant="caption" color="text.secondary">Profile Home Address</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>{userDetail.profile.address || 'No address logged.'}</Typography>

            <Typography variant="caption" color="text.secondary">About / Biography</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>{userDetail.profile.bio || 'No biography written.'}</Typography>

            <Divider sx={{ my: 3 }} />

            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>Direct Access Permissions</Typography>
            {userDetail.permissions.length === 0 ? (
              <Typography variant="body2" color="text.secondary">No direct permissions assigned.</Typography>
            ) : (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                {userDetail.permissions.map(p => (
                  <Chip key={p} label={p} size="small" variant="outlined" color="primary" />
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
export default UserDetails;
