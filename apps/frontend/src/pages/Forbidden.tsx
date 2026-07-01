import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Security as ShieldIcon } from '@mui/icons-material';

export const Forbidden: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', p: 2 }}>
      <Paper sx={{ 
        maxWidth: 500, 
        width: '100%', 
        p: 6, 
        textAlign: 'center', 
        bgcolor: 'background.paper', 
        border: '1px solid rgba(255,255,255,0.06)',
        backdropFilter: 'blur(16px)',
        borderRadius: 4
      }}>
        <ShieldIcon sx={{ fontSize: 80, color: 'secondary.main', mb: 3 }} />
        <Typography variant="h3" sx={{ fontFamily: 'Outfit', fontWeight: 800, color: '#f8fafc', mb: 2 }}>
          403 - Forbidden
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Access Denied. You do not possess the necessary role authorization permissions to access this secure zone.
        </Typography>
        <Button variant="contained" color="primary" size="large" onClick={() => navigate('/')}>
          Return to Console
        </Button>
      </Paper>
    </Box>
  );
};

export default Forbidden;
