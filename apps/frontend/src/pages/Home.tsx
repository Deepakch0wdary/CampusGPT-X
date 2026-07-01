import React, { useEffect, useState } from 'react';
import { 
  Typography, 
  Grid, 
  Paper, 
  Box, 
  Button, 
  CircularProgress, 
  Chip, 
  IconButton, 
  Divider 
} from '@mui/material';
import { 
  CheckCircle as CheckCircleIcon, 
  Error as ErrorIcon, 
  Refresh as RefreshIcon,
  GitHub as GitHubIcon
} from '@mui/icons-material';

interface HealthStatus {
  status: string;
  api: { status: string; latency_ms: number };
  database: { status: string; latency_ms: number | null };
}

export const Home: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/health');
      if (!response.ok) {
        throw new Error('API returned error status');
      }
      const data = await response.json();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to system API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <Box>
      {/* Welcome Banner */}
      <Box sx={{ mb: 6, p: 5, borderRadius: 3, background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', border: '1px solid rgba(255,255,255,0.08)' }}>
        <Typography variant="h3" sx={{ fontFamily: 'Outfit', mb: 2, fontWeight: 800 }}>
          CampusGPT <span className="text-blue-500">X</span>
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 400, mb: 3, maxWidth: 600 }}>
          The AI-Powered Smart Campus Operating System. Welcome to Day 1: Foundation and monorepo structure.
        </Typography>
        <Button 
          variant="contained" 
          size="large" 
          startIcon={<GitHubIcon />}
          sx={{ bgcolor: 'primary.main', '&:hover': { bgcolor: 'primary.dark' } }}
        >
          View System Architecture
        </Button>
      </Box>

      {/* Overview Grid */}
      <Grid container spacing={4}>
        {/* Status Monitoring */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 4, height: '100%', bgcolor: 'background.paper' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>
                System Diagnostics
              </Typography>
              <IconButton onClick={fetchHealth} disabled={loading} size="small" color="primary">
                <RefreshIcon />
              </IconButton>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 2 }}>
                <CircularProgress size={20} />
                <Typography color="text.secondary" variant="body2">Querying orchestrator health...</Typography>
              </Box>
            ) : error ? (
              <Box sx={{ p: 2, bgcolor: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.2)', borderRadius: 2, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <ErrorIcon color="error" />
                <Typography variant="body2" color="error.light">
                  Connection degraded. Local FastAPI server offline.
                </Typography>
              </Box>
            ) : health ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Global State:</Typography>
                  <Chip 
                    label={health.status.toUpperCase()} 
                    color={health.status === 'healthy' ? 'success' : 'warning'} 
                    size="small" 
                    icon={<CheckCircleIcon />}
                  />
                </Box>
                <Divider />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">API Gateway (FastAPI):</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {health.api.status} ({health.api.latency_ms}ms)
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">MySQL Database Connection:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {health.database.status} {health.database.latency_ms !== null ? `(${health.database.latency_ms}ms)` : ''}
                  </Typography>
                </Box>
              </Box>
            ) : null}
          </Paper>
        </Grid>

        {/* Directory details */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 4, height: '100%', bgcolor: 'background.paper' }}>
            <Typography variant="h5" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 3 }}>
              Folder Blueprint
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              CampusGPT X is structured to isolate responsibilities:
            </Typography>
            <ul className="space-y-3 text-sm text-slate-300 list-disc pl-5">
              <li><strong>apps/backend/</strong> — FastAPI server engine.</li>
              <li><strong>apps/frontend/</strong> — React, Vite SPA.</li>
              <li><strong>prisma/</strong> — Centralized ORM database models.</li>
              <li><strong>docker/</strong> — Isolated Docker configurations.</li>
            </ul>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
export default Home;
