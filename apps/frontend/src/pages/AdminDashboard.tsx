import React, { useEffect, useState } from 'react';
import { 
  Typography, 
  Grid, 
  Paper, 
  Box, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  CircularProgress, 
  Alert,
  Card,
  CardContent
} from '@mui/material';
import { 
  Security as SecurityIcon, 
  People as PeopleIcon, 
  History as HistoryIcon 
} from '@mui/icons-material';

interface AuditLog {
  id: string;
  user: string;
  action: string;
  details: string;
  ipAddress: string;
  createdAt: string;
}

export const AdminDashboard: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAudits = async () => {
    setLoading(true);
    setError(null);
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      setError('Authentication session not resolved.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/v1/audits', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to fetch audit trails.');
      }

      setLogs(data.logs);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudits();
  }, []);

  return (
    <Box>
      <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800, mb: 4 }}>
        Master Admin Command Center
      </Typography>

      {/* Grid Stats cards */}
      <Grid container spacing={3} sx={{ mb: 5 }}>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <PeopleIcon color="primary" sx={{ fontSize: 40 }} />
              <Box>
                <Typography color="text.secondary" variant="caption">Staff & Students</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>Workspace Active</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <SecurityIcon color="secondary" sx={{ fontSize: 40 }} />
              <Box>
                <Typography color="text.secondary" variant="caption">Authentication Model</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>RBAC Secured</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <HistoryIcon color="success" sx={{ fontSize: 40 }} />
              <Box>
                <Typography color="text.secondary" variant="caption">System Audit</Typography>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>Logs Active</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Audit Logs Table */}
      <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
        <Typography variant="h5" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 3 }}>
          System Audit Trail (Failed Attempts, User Creation, and Session Traces)
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Operator</Typography></TableCell>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Action Action</Typography></TableCell>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Details</Typography></TableCell>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>IP Address</Typography></TableCell>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Timestamp</Typography></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      <Typography color="text.secondary" sx={{ py: 2 }}>No audit entries resolved.</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>{log.user}</TableCell>
                      <TableCell>{log.action}</TableCell>
                      <TableCell>{log.details || 'No detail parameters.'}</TableCell>
                      <TableCell>{log.ipAddress || 'Internal'}</TableCell>
                      <TableCell>{new Date(log.createdAt).toLocaleString()}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  );
};
export default AdminDashboard;
