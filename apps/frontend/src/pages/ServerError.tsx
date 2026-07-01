import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { ReportGmailerrorred as ErrorIcon } from '@mui/icons-material';

export const ServerError: React.FC = () => {
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
        <ErrorIcon sx={{ fontSize: 80, color: 'secondary.main', mb: 3 }} />
        <Typography variant="h3" sx={{ fontFamily: 'Outfit', fontWeight: 800, color: '#f8fafc', mb: 2 }}>
          500 - Server Error
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          A severe internal database or server breakdown has occurred. Our engineering agents have been notified.
        </Typography>
        <Button variant="contained" color="primary" size="large" onClick={() => navigate('/')}>
          Return to Console
        </Button>
      </Paper>
    </Box>
  );
};

export default ServerError;
