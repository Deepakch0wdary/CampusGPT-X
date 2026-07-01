import React, { useEffect, useState } from 'react';
import { 
  Typography, 
  Paper, 
  Box, 
  TextField, 
  Button, 
  CircularProgress, 
  Alert,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  FormGroup,
  FormControlLabel,
  Checkbox
} from '@mui/material';

interface Role {
  id: string;
  name: string;
}

export const CreateUser: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loadingRoles, setLoadingRoles] = useState(true);
  
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  
  // Direct permission checkboxes
  const [customPermissions, setCustomPermissions] = useState<string[]>([]);
  
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<{ username: string; tempPwd: string } | null>(null);

  const availablePermissions = [
    { name: 'users:create', desc: 'Create new users' },
    { name: 'users:read', desc: 'View user directory' },
    { name: 'users:update', desc: 'Update user profiles' },
    { name: 'users:delete', desc: 'Delete user accounts' },
    { name: 'roles:manage', desc: 'Administer RBAC roles' },
    { name: 'sessions:manage', desc: 'View device sessions' },
    { name: 'audits:read', desc: 'Read trace audit logs' }
  ];

  const fetchRoles = async () => {
    setLoadingRoles(true);
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch('/api/v1/users/roles', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        // Exclude MASTER_ADMIN from the selectable role list to prevent duplicates
        setRoles(data.roles.filter((r: Role) => r.name !== 'MASTER_ADMIN'));
      }
    } catch (err) {
      console.error('Failed to fetch roles:', err);
    } finally {
      setLoadingRoles(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handlePermissionChange = (permName: string) => {
    if (customPermissions.includes(permName)) {
      setCustomPermissions(customPermissions.filter(p => p !== permName));
    } else {
      setCustomPermissions([...customPermissions, permName]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccessData(null);

    const token = localStorage.getItem('access_token');
    
    try {
      const response = await fetch('/api/v1/users', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name,
          email,
          role_name: selectedRole,
          department_id: selectedDept || null,
          permissions: customPermissions
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to create user account.');
      }

      setSuccessData({
        username: data.user.username,
        tempPwd: data.temporary_password
      });

      // Clear input fields
      setName('');
      setEmail('');
      setSelectedRole('');
      setSelectedDept('');
      setCustomPermissions([]);

    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 680, mx: 'auto' }}>
      <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800, mb: 4 }}>
        Provision Campus Account
      </Typography>

      {successData && (
        <Alert severity="success" sx={{ mb: 4, borderRadius: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
            User Account Created Successfully!
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1.5, my: 1, border: '1px solid rgba(255,255,255,0.05)' }}>
            <Typography variant="body2"><strong>Generated Username:</strong> {successData.username}</Typography>
            <Typography variant="body2"><strong>Temporary Password:</strong> {successData.tempPwd}</Typography>
          </Box>
          <Typography variant="caption" color="text.secondary">
            * These credentials have been logged. The user will be prompted to change their password on first login.
          </Typography>
        </Alert>
      )}

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
        <form onSubmit={handleSubmit}>
          <TextField
            label="Full Name"
            variant="outlined"
            fullWidth
            margin="normal"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            InputLabelProps={{ shrink: true }}
            placeholder="e.g. Professor Smith"
          />

          <TextField
            label="Email Address (Gmail)"
            type="email"
            variant="outlined"
            fullWidth
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            InputLabelProps={{ shrink: true }}
            placeholder="e.g. smith@gmail.com"
          />

          <FormControl fullWidth margin="normal" required>
            <InputLabel shrink id="role-select-label">Account Role</InputLabel>
            {loadingRoles ? (
              <Box sx={{ py: 1, px: 2 }}><CircularProgress size={20} /></Box>
            ) : (
              <Select
                labelId="role-select-label"
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                label="Account Role"
                displayEmpty
              >
                <MenuItem value="" disabled>Select target role...</MenuItem>
                {roles.map((r) => (
                  <MenuItem key={r.id} value={r.name}>{r.name}</MenuItem>
                ))}
              </Select>
            )}
          </FormControl>

          {/* Direct Custom Permissions Mapping */}
          <Box sx={{ mt: 3, mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Assign Direct Permissions (Optional)
            </Typography>
            <FormGroup row>
              {availablePermissions.map((perm) => (
                <FormControlLabel
                  key={perm.name}
                  control={
                    <Checkbox
                      checked={customPermissions.includes(perm.name)}
                      onChange={() => handlePermissionChange(perm.name)}
                    />
                  }
                  label={`${perm.name} (${perm.desc})`}
                  sx={{ width: '48%', mb: 1 }}
                />
              ))}
            </FormGroup>
          </Box>

          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={submitting}
            sx={{ mt: 3, height: 48, px: 4 }}
          >
            {submitting ? <CircularProgress size={24} color="inherit" /> : 'Register & Email Credentials'}
          </Button>
        </form>
      </Paper>
    </Box>
  );
};
export default CreateUser;
