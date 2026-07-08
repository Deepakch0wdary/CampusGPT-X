import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, Button, Stack, Chip,
  Alert, CircularProgress, TextField, MenuItem, Select, FormControl,
  InputLabel, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Tab, Tabs, Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import {
  Business, Work, BarChart, History, Add, Visibility
} from '@mui/icons-material';


const api = async (path: string, method = 'GET', body?: any) => {
  const token = localStorage.getItem('access_token');
  const res = await fetch(`/api/v1/placements${path}`, {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  return res.json();
};

const PlacementAdmin: React.FC = () => {
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<any>(null);
  const [companies, setCompanies] = useState<any[]>([]);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Dialog states
  const [companyDialog, setCompanyDialog] = useState(false);
  const [oppDialog, setOppDialog] = useState(false);

  // Form states
  const [companyForm, setCompanyForm] = useState({ name: '', industry: '', website: '', description: '', hrEmail: '' });
  const [oppForm, setOppForm] = useState({ companyId: '', title: '', description: '', type: 'JOB', location: '', compensation: '', minCgpa: 0.0, maxBacklogs: 999 });

  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [analRes, compRes, oppRes, auditRes] = await Promise.all([
        api('/analytics/overview'),
        api('/companies'),
        api('/opportunities?status=OPEN'),
        api('/audit')
      ]);
      if (analRes.success) setAnalytics(analRes.data);
      if (compRes.success) setCompanies(compRes.data || []);
      if (oppRes.success) setOpportunities(oppRes.data || []);
      if (auditRes.success) setAuditLogs(auditRes.data?.audits || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleCreateCompany = async () => {
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const res = await api('/companies', 'POST', companyForm);
      if (res.success) {
        setSuccessMsg('Company created successfully!');
        setCompanyDialog(false);
        setCompanyForm({ name: '', industry: '', website: '', description: '', hrEmail: '' });
        fetchAll();
      } else {
        setErrorMsg(res.message || 'Failed to create company.');
      }
    } catch (e) {
      setErrorMsg('Network error.');
    }
  };

  const handleCreateOpp = async () => {
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const res = await api('/opportunities', 'POST', oppForm);
      if (res.success) {
        setSuccessMsg('Opportunity created successfully!');
        setOppDialog(false);
        setOppForm({ companyId: '', title: '', description: '', type: 'JOB', location: '', compensation: '', minCgpa: 0.0, maxBacklogs: 999 });
        fetchAll();
      } else {
        setErrorMsg(res.message || 'Failed to create opportunity.');
      }
    } catch (e) {
      setErrorMsg('Network error.');
    }
  };

  if (loading) {
    return (
      <Box p={4} display="flex" flexDirection="column" alignItems="center" gap={2}>
        <CircularProgress size={48} />
        <Typography color="text.secondary">Loading Placement Administration Panel...</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight="bold" color="primary" gutterBottom>
        Placement Officer Administration Panel
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Manage placement drives, companies, job opportunities, applications, and view enterprise placement analytics.
      </Typography>

      {successMsg && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMsg('')}>{successMsg}</Alert>}
      {errorMsg && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setErrorMsg('')}>{errorMsg}</Alert>}

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label="Analytics Overview" icon={<BarChart />} iconPosition="start" />
        <Tab label="Companies" icon={<Business />} iconPosition="start" />
        <Tab label="Opportunities" icon={<Work />} iconPosition="start" />
        <Tab label="Audit Logs" icon={<History />} iconPosition="start" />
      </Tabs>

      {/* Tab 0: Analytics */}
      {tab === 0 && analytics && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card raised>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>Total Active Companies</Typography>
                <Typography variant="h4" fontWeight="bold">{analytics.totalActiveCompanies}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card raised>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>Open Opportunities</Typography>
                <Typography variant="h4" fontWeight="bold">{analytics.totalOpenOpportunities}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card raised>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>Placed Students</Typography>
                <Typography variant="h4" fontWeight="bold">{analytics.placedStudents}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card raised>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>Placement Rate</Typography>
                <Typography variant="h4" fontWeight="bold">{analytics.placementRate}%</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tab 1: Companies */}
      {tab === 1 && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Stack direction="row" justifyContent="space-between" mb={2}>
            <Typography variant="h6" fontWeight="bold">Companies Directory</Typography>
            <Button variant="contained" startIcon={<Add />} onClick={() => setCompanyDialog(true)}>Add Company</Button>
          </Stack>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Company Name</TableCell>
                  <TableCell>Industry</TableCell>
                  <TableCell>Website</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {companies.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{c.name}</TableCell>
                    <TableCell>{c.industry}</TableCell>
                    <TableCell>{c.website || 'N/A'}</TableCell>
                    <TableCell>
                      <Button size="small" startIcon={<Visibility />}>View Detials</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Tab 2: Opportunities */}
      {tab === 2 && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Stack direction="row" justifyContent="space-between" mb={2}>
            <Typography variant="h6" fontWeight="bold">Opportunities Directory</Typography>
            <Button variant="contained" startIcon={<Add />} onClick={() => setOppDialog(true)}>Create Opportunity</Button>
          </Stack>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Title</TableCell>
                  <TableCell>Company</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Compensation</TableCell>
                  <TableCell>Min CGPA</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {opportunities.map((o) => (
                  <TableRow key={o.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{o.title}</TableCell>
                    <TableCell>{o.companyName}</TableCell>
                    <TableCell>
                      <Chip label={o.type} size="small" color={o.type === 'JOB' ? 'primary' : 'secondary'} />
                    </TableCell>
                    <TableCell>{o.compensation}</TableCell>
                    <TableCell>{o.minCgpa}</TableCell>
                    <TableCell>
                      <Chip label={o.status} size="small" color="success" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Tab 3: Audits */}
      {tab === 3 && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight="bold" gutterBottom>Placement Audit Trail</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Action</TableCell>
                  <TableCell>Entity Type</TableCell>
                  <TableCell>Entity ID</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {auditLogs.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{a.action}</TableCell>
                    <TableCell>{a.entityType}</TableCell>
                    <TableCell>{a.entityId || 'N/A'}</TableCell>
                    <TableCell>{new Date(a.createdAt).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Add Company Dialog */}
      <Dialog open={companyDialog} onClose={() => setCompanyDialog(false)}>
        <DialogTitle>Add New Company</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField label="Name" fullWidth value={companyForm.name} onChange={e => setCompanyForm({...companyForm, name: e.target.value})} />
            <TextField label="Industry" fullWidth value={companyForm.industry} onChange={e => setCompanyForm({...companyForm, industry: e.target.value})} />
            <TextField label="Website" fullWidth value={companyForm.website} onChange={e => setCompanyForm({...companyForm, website: e.target.value})} />
            <TextField label="HR Email" fullWidth value={companyForm.hrEmail} onChange={e => setCompanyForm({...companyForm, hrEmail: e.target.value})} />
            <TextField label="Description" multiline rows={3} fullWidth value={companyForm.description} onChange={e => setCompanyForm({...companyForm, description: e.target.value})} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompanyDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateCompany}>Create</Button>
        </DialogActions>
      </Dialog>

      {/* Create Opportunity Dialog */}
      <Dialog open={oppDialog} onClose={() => setOppDialog(false)}>
        <DialogTitle>Create Opportunity</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <FormControl fullWidth>
              <InputLabel>Company</InputLabel>
              <Select value={oppForm.companyId} label="Company" onChange={e => setOppForm({...oppForm, companyId: e.target.value})}>
                {companies.map(c => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
              </Select>
            </FormControl>
            <TextField label="Title" fullWidth value={oppForm.title} onChange={e => setOppForm({...oppForm, title: e.target.value})} />
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select value={oppForm.type} label="Type" onChange={e => setOppForm({...oppForm, type: e.target.value})}>
                <MenuItem value="JOB">Job</MenuItem>
                <MenuItem value="INTERNSHIP">Internship</MenuItem>
              </Select>
            </FormControl>
            <TextField label="Location" fullWidth value={oppForm.location} onChange={e => setOppForm({...oppForm, location: e.target.value})} />
            <TextField label="Compensation" fullWidth value={oppForm.compensation} onChange={e => setOppForm({...oppForm, compensation: e.target.value})} />
            <TextField label="Min CGPA" type="number" fullWidth value={oppForm.minCgpa} onChange={e => setOppForm({...oppForm, minCgpa: parseFloat(e.target.value) || 0.0})} />
            <TextField label="Max Backlogs" type="number" fullWidth value={oppForm.maxBacklogs} onChange={e => setOppForm({...oppForm, maxBacklogs: parseInt(e.target.value) || 0})} />
            <TextField label="Description" multiline rows={3} fullWidth value={oppForm.description} onChange={e => setOppForm({...oppForm, description: e.target.value})} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOppDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateOpp}>Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PlacementAdmin;
