import React, { useEffect, useState } from 'react';
import { 
  Typography, 
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
  Chip
} from '@mui/material';

interface UserItem {
  id: string;
  name: string;
  username: string;
  email: string;
  role: string;
  isSuspended: boolean;
  isDisabled: boolean;
  createdAt: string;
}

export const UserList: React.FC = () => {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      setError('Active session not resolved.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/v1/users', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to fetch user profiles.');
      }

      setUsers(data.users);
    } catch (err: any) {
      setError(err.message || 'Failed to load user directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return (
    <Box>
      <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800, mb: 4 }}>
        Campus Directory
      </Typography>

      <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
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
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Name</Typography></TableCell>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Username</Typography></TableCell>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Email Address</Typography></TableCell>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>System Role</Typography></TableCell>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Status</Typography></TableCell>
                  <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Created Date</Typography></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography color="text.secondary" sx={{ py: 2 }}>No users found.</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell sx={{ fontWeight: 500 }}>{u.name}</TableCell>
                      <TableCell>{u.username}</TableCell>
                      <TableCell>{u.email}</TableCell>
                      <TableCell>
                        <Chip 
                          label={u.role} 
                          color={u.role === 'MASTER_ADMIN' ? 'secondary' : 'default'} 
                          size="small" 
                        />
                      </TableCell>
                      <TableCell>
                        {u.isDisabled || u.isSuspended ? (
                          <Chip label="INACTIVE" color="error" size="small" variant="outlined" />
                        ) : (
                          <Chip label="ACTIVE" color="success" size="small" variant="outlined" />
                        )}
                      </TableCell>
                      <TableCell>{new Date(u.createdAt).toLocaleDateString()}</TableCell>
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
export default UserList;
