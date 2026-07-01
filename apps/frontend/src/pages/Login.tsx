import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  CircularProgress, 
  Alert 
} from '@mui/material';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username_or_email: usernameOrEmail,
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || 'Login failed. Verify credentials.');
      }

      // Store auth state
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      if (data.must_change_password) {
        navigate('/change-password');
      } else {
        navigate(data.user.role === 'MASTER_ADMIN' ? '/dashboard' : '/');
      }
      
      // Dispatch storage event to notify Layout or other listeners
      window.dispatchEvent(new Event('storage'));
    } catch (err: any) {
      setError(err.message || 'An error occurred during authentication.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 128px)' }}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 420, border: '1px solid rgba(255, 255, 255, 0.08)', bgcolor: 'background.paper' }}>
        <Box sx={{ textCenter: 'center', mb: 3 }}>
          <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800, color: 'primary.main', mb: 1, textAlign: 'center' }}>
            CampusGPT <span style={{ color: '#fff' }}>X</span>
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
            Verify identity to access campus resources.
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            label="Email or Username"
            variant="outlined"
            fullWidth
            margin="normal"
            value={usernameOrEmail}
            onChange={(e) => setUsernameOrEmail(e.target.value)}
            required
            InputLabelProps={{ shrink: true }}
            placeholder="e.g. admin"
          />

          <TextField
            label="Password"
            type="password"
            variant="outlined"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            InputLabelProps={{ shrink: true }}
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            disabled={loading}
            sx={{ mt: 3, mb: 2, height: 48 }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Authenticate Session'}
          </Button>
        </form>

        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
          <Link to="/forgot-password" style={{ textDecoration: 'none', color: '#0070f3', fontSize: '14px', fontWeight: 500 }}>
            Forgot password?
          </Link>
        </Box>
      </Paper>
    </Box>
  );
};
export default Login;
