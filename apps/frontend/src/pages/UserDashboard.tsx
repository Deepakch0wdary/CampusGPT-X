import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Grid, 
  Paper, 
  Button, 
  Dialog,
  DialogContent,
  Card,
  CardContent
} from '@mui/material';
import { 
  PersonAdd as PersonAddIcon, 
  UploadFile as ImportIcon, 
  Download as ExportIcon,
  People as PeopleIcon,
  VerifiedUser as VerifiedIcon,
  Block as BlockIcon
} from '@mui/icons-material';
import UserTable from './UserTable';
import UserForm from './UserForm';

export const UserDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  
  // Dialog controls
  const [formOpen, setFormOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  const triggerRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleEditClick = (id: string) => {
    setSelectedUserId(id);
    setFormOpen(true);
  };

  const handleCreateClick = () => {
    setSelectedUserId(null);
    setFormOpen(true);
  };

  const handleViewClick = (id: string) => {
    navigate(`/users/${id}`);
  };

  const handleFormSuccess = () => {
    setFormOpen(false);
    triggerRefresh();
  };

  const handleExportClick = () => {
    // Directly hits browser stream download endpoint
    const token = localStorage.getItem('access_token');
    window.open(`/api/v1/users/export/xlsx?token=${token}`, '_blank');
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800 }}>
          User Provisioning & Directory
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button 
            variant="contained" 
            startIcon={<PersonAddIcon />} 
            onClick={handleCreateClick}
          >
            Provision User
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<ImportIcon />}
            onClick={() => navigate('/import-users')}
          >
            Excel Bulk Import
          </Button>
          <Button 
            variant="outlined" 
            color="success"
            startIcon={<ExportIcon />}
            onClick={handleExportClick}
          >
            Export Directory
          </Button>
        </Box>
      </Box>

      {/* Summary Diagnostics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.08)' }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <PeopleIcon color="primary" sx={{ fontSize: 40 }} />
              <Box>
                <Typography color="text.secondary" variant="caption">Total Directories</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>Roles Active</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.08)' }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <VerifiedIcon color="success" sx={{ fontSize: 40 }} />
              <Box>
                <Typography color="text.secondary" variant="caption">Account Security Status</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>2FA & Locked Guards</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.08)' }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <BlockIcon color="error" sx={{ fontSize: 40 }} />
              <Box>
                <Typography color="text.secondary" variant="caption">Suspended Access</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>Locks Monitored</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Primary Directory Data Grid */}
      <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
        <UserTable 
          onEditClick={handleEditClick} 
          onViewClick={handleViewClick} 
          refreshTrigger={refreshTrigger} 
        />
      </Paper>

      {/* Dynamic Creation / Edit Modal Dialog */}
      <Dialog 
        open={formOpen} 
        onClose={() => setFormOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogContent sx={{ bgcolor: 'background.paper', p: 4 }}>
          <UserForm 
            userId={selectedUserId} 
            onSuccess={handleFormSuccess} 
            onCancel={() => setFormOpen(false)} 
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};
export default UserDashboard;
