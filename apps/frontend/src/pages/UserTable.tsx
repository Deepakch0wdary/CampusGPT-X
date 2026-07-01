import React, { useEffect, useState } from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  TextField, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Pagination, 
  Box, 
  Typography, 
  Button, 
  Checkbox, 
  IconButton, 
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import { 
  Edit as EditIcon, 
  Delete as DeleteIcon, 
  Visibility as ViewIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

interface UserItem {
  id: string;
  name: string;
  username: string;
  email: string;
  role: string;
  status: string;
  department: string | null;
  section: string | null;
  createdAt: string;
}

interface UserTableProps {
  onEditClick: (id: string) => void;
  onViewClick: (id: string) => void;
  refreshTrigger: number;
}

export const UserTable: React.FC<UserTableProps> = ({ onEditClick, onViewClick, refreshTrigger }) => {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Listing state variables
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  
  // Sort variables
  const [sortBy, setSortBy] = useState('createdAt');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Checkbox variables
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Dialog triggers
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [bulkStatusTarget, setBulkStatusTarget] = useState<string | null>(null);

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
      const queryParams = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      if (search) queryParams.append('search', search);
      if (selectedRole) queryParams.append('role', selectedRole);
      if (selectedStatus) queryParams.append('status', selectedStatus);

      const response = await fetch(`/api/v1/users?${queryParams.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to fetch user profiles.');
      }

      setUsers(data.users);
      setTotalPages(data.pages);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve listings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, search, selectedRole, selectedStatus, sortBy, sortOrder, refreshTrigger]);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      const pageUserIds = users.filter(u => u.role !== 'MASTER_ADMIN').map(u => u.id);
      setSelectedIds(pageUserIds);
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(x => x !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteId) return;
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(`/api/v1/users/${deleteId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error?.message || 'Purging failed.');
      }
      setDeleteId(null);
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleBulkStatusChange = async () => {
    if (!bulkStatusTarget || selectedIds.length === 0) return;
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch('/api/v1/users/status', {
        method: 'PATCH',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_ids: selectedIds,
          status: bulkStatusTarget
        })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error?.message || 'Status update failed.');
      }
      setSelectedIds([]);
      setBulkStatusTarget(null);
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const rolesList = [
    'TEACHER', 'MENTOR', 'PLACEMENT_OFFICER', 'ADMISSION_OFFICE', 
    'STUDENT', 'PARENT', 'ALUMNI', 'LIBRARIAN', 'HOSTEL_MANAGER', 'TRANSPORT_MANAGER'
  ];

  return (
    <Box>
      {/* Search & Filters Controls */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3, alignItems: 'center' }}>
        <TextField
          size="small"
          label="Search directory..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ minWidth: 260 }}
          InputProps={{ endAdornment: <SearchIcon color="action" /> }}
        />

        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Filter Role</InputLabel>
          <Select
            value={selectedRole}
            label="Filter Role"
            onChange={(e) => setSelectedRole(e.target.value)}
          >
            <MenuItem value="">All Roles</MenuItem>
            {rolesList.map(r => <MenuItem key={r} value={r}>{r}</MenuItem>)}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Filter Status</InputLabel>
          <Select
            value={selectedStatus}
            label="Filter Status"
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="ACTIVE">ACTIVE</MenuItem>
            <MenuItem value="SUSPENDED">SUSPENDED</MenuItem>
            <MenuItem value="DISABLED">DISABLED</MenuItem>
            <MenuItem value="PENDING">PENDING</MenuItem>
          </Select>
        </FormControl>

        <IconButton onClick={fetchUsers} size="small" color="primary" sx={{ ml: 'auto' }}>
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* Bulk Operations Toolbar */}
      {selectedIds.length > 0 && (
        <Box sx={{ p: 2, mb: 2, bgcolor: 'rgba(25, 118, 210, 0.08)', borderRadius: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2">{selectedIds.length} accounts selected</Typography>
          <Button size="small" variant="outlined" color="warning" onClick={() => setBulkStatusTarget('SUSPENDED')}>
            Suspend Selected
          </Button>
          <Button size="small" variant="outlined" color="success" onClick={() => setBulkStatusTarget('ACTIVE')}>
            Activate Selected
          </Button>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}><CircularProgress /></Box>
      ) : (
        <TableContainer component={Paper} sx={{ bgcolor: 'background.paper' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox 
                    indeterminate={selectedIds.length > 0 && selectedIds.length < users.filter(u => u.role !== 'MASTER_ADMIN').length}
                    checked={users.length > 0 && selectedIds.length === users.filter(u => u.role !== 'MASTER_ADMIN').length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell sx={{ cursor: 'pointer' }} onClick={() => handleSort('name')}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Name {sortBy === 'name' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
                  </Typography>
                </TableCell>
                <TableCell sx={{ cursor: 'pointer' }} onClick={() => handleSort('username')}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Username {sortBy === 'username' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
                  </Typography>
                </TableCell>
                <TableCell sx={{ cursor: 'pointer' }} onClick={() => handleSort('email')}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Email {sortBy === 'email' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
                  </Typography>
                </TableCell>
                <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Role</Typography></TableCell>
                <TableCell><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Status</Typography></TableCell>
                <TableCell align="right"><Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Actions</Typography></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary" sx={{ py: 3 }}>No users matches these filters.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                users.map((u) => (
                  <TableRow key={u.id} hover selected={selectedIds.includes(u.id)}>
                    <TableCell padding="checkbox">
                      {u.role !== 'MASTER_ADMIN' && (
                        <Checkbox 
                          checked={selectedIds.includes(u.id)}
                          onChange={() => handleSelectOne(u.id)}
                        />
                      )}
                    </TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>{u.name}</TableCell>
                    <TableCell>{u.username}</TableCell>
                    <TableCell>{u.email}</TableCell>
                    <TableCell>
                      <Chip label={u.role} size="small" color={u.role === 'MASTER_ADMIN' ? 'secondary' : 'default'} />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={u.status} 
                        size="small" 
                        color={u.status === 'ACTIVE' ? 'success' : u.status === 'SUSPENDED' ? 'warning' : 'error'} 
                        variant="outlined" 
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton onClick={() => onViewClick(u.id)} size="small" color="info"><ViewIcon /></IconButton>
                      {u.role !== 'MASTER_ADMIN' && (
                        <>
                          <IconButton onClick={() => onEditClick(u.id)} size="small" color="primary"><EditIcon /></IconButton>
                          <IconButton onClick={() => setDeleteId(u.id)} size="small" color="error"><DeleteIcon /></IconButton>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Pagination wrapper */}
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
        <Pagination count={totalPages} page={page} onChange={(_, p) => setPage(p)} color="primary" />
      </Box>

      {/* Single Delete Confirmation Dialog */}
      <Dialog open={!!deleteId} onClose={() => setDeleteId(null)}>
        <DialogTitle>Purge Account</DialogTitle>
        <DialogContent>Are you sure you want to delete this user? This action is irreversible.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteId(null)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error">Purge</Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Status Update Dialog */}
      <Dialog open={!!bulkStatusTarget} onClose={() => setBulkStatusTarget(null)}>
        <DialogTitle>Update Statuses</DialogTitle>
        <DialogContent>Apply state changes to selected accounts?</DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkStatusTarget(null)}>Cancel</Button>
          <Button onClick={handleBulkStatusChange} color="primary">Apply</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
export default UserTable;
