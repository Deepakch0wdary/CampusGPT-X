import React, { useEffect, useState } from 'react';
import { 
  Typography, 
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

interface UserFormProps {
  userId?: string | null;
  onSuccess: () => void;
  onCancel: () => void;
}

interface Role {
  id: string;
  name: string;
}

export const UserForm: React.FC<UserFormProps> = ({ userId, onSuccess, onCancel }) => {
  const isEdit = !!userId;

  const [roles, setRoles] = useState<Role[]>([]);
  const [loadingConfig, setLoadingConfig] = useState(true);

  // Form State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  
  // Custom Profile Attributes
  const [phone, setPhone] = useState('');
  const [bio, setBio] = useState('');
  const [address, setAddress] = useState('');
  
  const [customPermissions, setCustomPermissions] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<{ username: string; temp: string } | null>(null);

  const availablePermissions = [
    { name: 'users:create', desc: 'Create new users' },
    { name: 'users:read', desc: 'View user directory' },
    { name: 'users:update', desc: 'Update user profiles' },
    { name: 'users:delete', desc: 'Delete user accounts' },
    { name: 'roles:manage', desc: 'Administer RBAC roles' },
    { name: 'sessions:manage', desc: 'View device sessions' },
    { name: 'audits:read', desc: 'Read trace audit logs' }
  ];

  const fetchConfigs = async () => {
    setLoadingConfig(true);
    const token = localStorage.getItem('access_token');
    try {
      // 1. Roles
      const rResp = await fetch('/api/v1/users/roles', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const rData = await rResp.json();
      if (rResp.ok) {
        setRoles(rData.roles.filter((r: Role) => r.name !== 'MASTER_ADMIN'));
      }

      // 2. Fetch user profile if in Edit mode
      if (isEdit) {
        const uResp = await fetch(`/api/v1/users/${userId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const uData = await uResp.json();
        if (uResp.ok) {
          setName(uData.user.name);
          setEmail(uData.user.email);
          setSelectedRole(uData.user.role);
          setPhone(uData.user.profile.phoneNumber || '');
          setBio(uData.user.profile.bio || '');
          setAddress(uData.user.profile.address || '');
          setCustomPermissions(uData.user.permissions || []);
        }
      }
    } catch (err) {
      console.error('Failed to load configs:', err);
    } finally {
      setLoadingConfig(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, [userId]);

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
    setCredentials(null);

    const token = localStorage.getItem('access_token');
    
    try {
      if (isEdit) {
        // Edit Action
        const response = await fetch(`/api/v1/users/${userId}`, {
          method: 'PUT',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            name,
            email,
            phone_number: phone || null,
            bio: bio || null,
            address: address || null
          }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error?.message || 'Failed to update user.');
        
        onSuccess();
      } else {
        // Create Action
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
            permissions: customPermissions
          }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error?.message || 'Failed to create user.');

        setCredentials({
          username: data.user.username,
          temp: data.temporary_password
        });
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 580, mx: 'auto' }}>
      <Typography variant="h5" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 3 }}>
        {isEdit ? 'Modify Account Details' : 'Provision User Account'}
      </Typography>

      {credentials && (
        <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
            User Account Successfully Spawned!
          </Typography>
          <Box sx={{ bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1, my: 1 }}>
            <Typography variant="body2"><strong>Username:</strong> {credentials.username}</Typography>
            <Typography variant="body2"><strong>Temporary Password:</strong> {credentials.temp}</Typography>
          </Box>
          <Typography variant="caption">
            * Share these values with the user. They will be forced to change their password on first login.
          </Typography>
        </Alert>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loadingConfig ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress /></Box>
      ) : (
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
            placeholder="e.g. Professor Green"
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
            placeholder="e.g. green@gmail.com"
          />

          {!isEdit && (
            <FormControl fullWidth margin="normal" required>
              <InputLabel shrink id="role-select-label">Account Role</InputLabel>
              <Select
                labelId="role-select-label"
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                label="Account Role"
                displayEmpty
              >
                <MenuItem value="" disabled>Choose role type...</MenuItem>
                {roles.map((r) => (
                  <MenuItem key={r.id} value={r.name}>{r.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          {isEdit && (
            <>
              <TextField
                label="Phone Number"
                variant="outlined"
                fullWidth
                margin="normal"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="Home Address"
                variant="outlined"
                fullWidth
                margin="normal"
                multiline
                rows={2}
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="Short Bio"
                variant="outlined"
                fullWidth
                margin="normal"
                multiline
                rows={2}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </>
          )}

          {!isEdit && (
            <Box sx={{ mt: 3, mb: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                Direct Permissions Checkboxes (Optional)
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
                    label={perm.name}
                    sx={{ width: '48%' }}
                  />
                ))}
              </FormGroup>
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: 2, mt: 4 }}>
            <Button
              type="submit"
              variant="contained"
              disabled={submitting}
              sx={{ height: 40, px: 4 }}
            >
              {submitting ? <CircularProgress size={20} color="inherit" /> : (isEdit ? 'Save Changes' : 'Create User')}
            </Button>
            <Button
              variant="outlined"
              onClick={onCancel}
              sx={{ height: 40 }}
            >
              {credentials ? 'Finished' : 'Cancel'}
            </Button>
          </Box>
        </form>
      )}
    </Box>
  );
};
export default UserForm;
