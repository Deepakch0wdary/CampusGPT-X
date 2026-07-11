import React, { useState, useEffect } from 'react';
import { Box, Typography, Alert, CircularProgress } from '@mui/material';
import { StudentFinanceDashboard } from './StudentFinanceDashboard';
import { ParentFinanceDashboard } from './ParentFinanceDashboard';
import { FinanceAdminDashboard } from './FinanceAdminDashboard';

export const FeeDashboard: React.FC = () => {
  const [role, setRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const uStr = localStorage.getItem('user');
      if (uStr) {
        const user = JSON.parse(uStr);
        if (user && user.role && user.role.name) {
          setRole(user.role.name);
        }
      }
    } catch (e) {
      console.error("Failed to parse user session storage", e);
    } finally {
      setLoading(false);
    }
  }, []);

  if (loading) {
    return (
      <Box p={4} display="flex" justifyContent="center">
        <CircularProgress />
      </Box>
    );
  }

  // Render role-appropriate dashboards
  if (role === 'STUDENT') {
    return <StudentFinanceDashboard />;
  }

  if (role === 'PARENT') {
    return <ParentFinanceDashboard />;
  }

  if (role === 'MASTER_ADMIN' || role === 'FINANCE_OFFICE') {
    return <FinanceAdminDashboard />;
  }

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 2 }}>Financial Management</Typography>
      <Alert severity="error">
        Access denied. Your system role ({role || 'UNKNOWN'}) is not authorized to view financial statements.
      </Alert>
    </Box>
  );
};
export default FeeDashboard;
