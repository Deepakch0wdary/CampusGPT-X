import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  CircularProgress, 
  Alert 
} from '@mui/material';

export const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to submit reset request.');
      }

      setSuccess('Verification request registered. If you are using the local mock sandbox, please extract your password reset token from the system console output.');
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 128px)' }}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 420, border: '1px solid rgba(255, 255, 255, 0.08)', bgcolor: 'background.paper' }}>
        <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800, color: 'primary.main', mb: 2, textAlign: 'center' }}>
          Reset Password
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
          Enter your registered email address to receive recovery tokens.
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2, borderRadius: 2 }}>{success}</Alert>}

        <form onSubmit={handleSubmit}>
          <TextField
            label="Email Address"
            type="email"
            variant="outlined"
            fullWidth
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            InputLabelProps={{ shrink: true }}
            placeholder="e.g. user@gmail.com"
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            disabled={loading}
            sx={{ mt: 3, mb: 2, height: 48 }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Request Recovery Token'}
          </Button>
        </form>

        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
          <Link to="/login" style={{ textDecoration: 'none', color: '#0070f3', fontSize: '14px', fontWeight: 500 }}>
            Back to login
          </Link>
        </Box>
      </Paper>
    </Box>
  );
};
export default ForgotPassword;
