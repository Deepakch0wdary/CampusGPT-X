import React from 'react';
import { Paper, Typography, Box } from '@mui/material';
import { InfoOutlined } from '@mui/icons-material';

export const AcademicMentorDisclaimer: React.FC = () => {
  return (
    <Paper sx={{ p: 2, bgcolor: 'rgba(255, 245, 157, 0.15)', border: '1px solid #ffd54f', mt: 3, mb: 2, borderRadius: 2 }}>
      <Box display="flex" alignItems="center" gap={1.5}>
        <InfoOutlined color="warning" />
        <Typography variant="body2" color="textSecondary">
          Academic insights are advisory and generated from available academic records. They do not make automated grading, disciplinary, admission, or other high-stakes decisions.
          <br />
          <strong>Engine: Local Explainable Analytics (LOCAL_EXPLAINABLE_ANALYTICS)</strong>
        </Typography>
      </Box>
    </Paper>
  );
};
export default AcademicMentorDisclaimer;
