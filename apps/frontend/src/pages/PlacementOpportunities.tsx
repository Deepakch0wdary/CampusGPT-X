import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, Card, CardContent, CardActions,
  Button, Stack, Chip, Divider, Alert, CircularProgress,
  TextField, MenuItem, Select, FormControl, InputLabel,
  LinearProgress, Dialog, DialogTitle, DialogContent,
  DialogActions
} from '@mui/material';
import {
  Work, Business, LocationOn, AttachMoney, School,
  Info, Send, FilterList, Search, BarChart, Warning
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

const scoreColor = (score: number) => {
  if (score >= 75) return '#4caf50';
  if (score >= 50) return '#ff9800';
  if (score >= 25) return '#f44336';
  return '#9e9e9e';
};

const PlacementOpportunities: React.FC = () => {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [selectedOpp, setSelectedOpp] = useState<any>(null);
  const [matchResult, setMatchResult] = useState<any>(null);

  const [applyDialog, setApplyDialog] = useState(false);
  const [detailDialog, setDetailDialog] = useState(false);
  const [applying, setApplying] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchOpps = async () => {
    setLoading(true);
    try {
      let url = '/opportunities?';
      if (typeFilter) url += `type=${typeFilter}&`;
      if (search) url += `search=${encodeURIComponent(search)}&`;
      const res = await api(url);
      if (res.success) setOpportunities(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOpps(); }, [typeFilter]);

  const handleSearch = () => fetchOpps();

  const handleViewDetail = async (opp: any) => {
    setSelectedOpp(opp);
    setMatchResult(null);
    setDetailDialog(true);
    // Fetch match score
    const matchRes = await api(`/matches/me/${opp.id}`);
    if (matchRes.success) setMatchResult(matchRes.data);
  };


  const handleApply = async () => {
    if (!selectedOpp) return;
    setApplying(true);
    setErrorMsg('');
    try {
      const res = await api('/applications', 'POST', { opportunityId: selectedOpp.id });
      if (res.success) {
        setSuccessMsg(`Application submitted for "${selectedOpp.title}"!`);
        setApplyDialog(false);
        setDetailDialog(false);
      } else {
        setErrorMsg(res.message || 'Failed to apply.');
      }
    } catch (e) {
      setErrorMsg('Network error. Please try again.');
    } finally {
      setApplying(false);
    }
  };

  const factorBar = (label: string, value: number, contribution: number) => (
    <Box key={label} mb={1.5}>
      <Box display="flex" justifyContent="space-between">
        <Typography variant="caption">{label}</Typography>
        <Typography variant="caption" color="text.secondary">+{contribution.toFixed(1)}</Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={value * 100}
        sx={{ height: 6, borderRadius: 4 }}
        color={value > 0.6 ? 'success' : value > 0.3 ? 'warning' : 'error'}
      />
    </Box>
  );

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight="bold" color="primary" gutterBottom>
        Opportunities — Jobs & Internships
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Browse all open positions. Match scores are computed by <strong>LOCAL_EXPLAINABLE_CAREER_MATCHING</strong>.
      </Typography>

      {successMsg && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMsg('')}>{successMsg}</Alert>}
      {errorMsg && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setErrorMsg('')}>{errorMsg}</Alert>}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3, borderRadius: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="flex-end">
          <TextField
            label="Search Opportunities"
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && handleSearch()}
            size="small"
            InputProps={{ endAdornment: <Search sx={{ color: 'text.disabled' }} /> }}
            sx={{ flex: 1 }}
          />
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Type</InputLabel>
            <Select value={typeFilter} label="Type" onChange={e => setTypeFilter(e.target.value)}>
              <MenuItem value="">All</MenuItem>
              <MenuItem value="JOB">Job</MenuItem>
              <MenuItem value="INTERNSHIP">Internship</MenuItem>
            </Select>
          </FormControl>
          <Button variant="contained" startIcon={<FilterList />} onClick={handleSearch}>
            Filter
          </Button>
        </Stack>
      </Paper>

      {loading ? (
        <Box textAlign="center" py={6}>
          <CircularProgress />
        </Box>
      ) : opportunities.length === 0 ? (
        <Box textAlign="center" py={6}>
          <Work sx={{ fontSize: 64, color: 'text.disabled' }} />
          <Typography variant="h6" color="text.secondary" mt={2}>No open opportunities found.</Typography>
          <Typography variant="body2" color="text.disabled">Try clearing filters or check back later.</Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {opportunities.map((opp: any) => (
            <Grid item xs={12} sm={6} md={4} key={opp.id}>
              <Card
                raised
                sx={{
                  height: '100%', display: 'flex', flexDirection: 'column',
                  borderRadius: 3, transition: 'transform 0.2s',
                  '&:hover': { transform: 'translateY(-4px)' }
                }}
              >
                <CardContent sx={{ flex: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                    <Chip
                      label={opp.type}
                      size="small"
                      color={opp.type === 'JOB' ? 'primary' : 'secondary'}
                      sx={{ fontWeight: 'bold' }}
                    />
                    <Chip
                      label={opp.roleType}
                      size="small"
                      variant="outlined"
                    />
                  </Box>

                  <Typography variant="h6" fontWeight="bold" gutterBottom mt={1}>
                    {opp.title}
                  </Typography>
                  <Typography variant="body2" color="primary" fontWeight="bold" gutterBottom>
                    <Business sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                    {opp.companyName}
                  </Typography>

                  <Stack spacing={0.5} mt={1}>
                    <Typography variant="caption" color="text.secondary">
                      <LocationOn sx={{ fontSize: 12, verticalAlign: 'middle', mr: 0.5 }} />
                      {opp.location}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      <AttachMoney sx={{ fontSize: 12, verticalAlign: 'middle', mr: 0.5 }} />
                      {opp.compensation}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      <School sx={{ fontSize: 12, verticalAlign: 'middle', mr: 0.5 }} />
                      Min CGPA: {opp.minCgpa || 'Not specified'}
                    </Typography>
                  </Stack>

                  {opp.deadline && (
                    <Box mt={1}>
                      <Chip
                        label={`Deadline: ${new Date(opp.deadline).toLocaleDateString()}`}
                        size="small"
                        color="warning"
                        variant="outlined"
                      />
                    </Box>
                  )}
                </CardContent>

                <CardActions sx={{ p: 2, pt: 0, gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    fullWidth
                    startIcon={<Info />}
                    onClick={() => handleViewDetail(opp)}
                  >
                    View & Match
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    fullWidth
                    startIcon={<Send />}
                    onClick={() => { setSelectedOpp(opp); setApplyDialog(true); }}
                  >
                    Apply
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Detail + Match Dialog */}
      <Dialog open={detailDialog} onClose={() => setDetailDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h6" fontWeight="bold">{selectedOpp?.title}</Typography>
              <Typography variant="body2" color="text.secondary">{selectedOpp?.companyName}</Typography>
            </Box>
            <Chip
              label={selectedOpp?.type}
              color={selectedOpp?.type === 'JOB' ? 'primary' : 'secondary'}
            />
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3}>
            {/* Description */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Description</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-line' }}>
                {selectedOpp?.description}
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Stack spacing={1}>
                <Typography variant="body2"><LocationOn sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5, color: 'text.secondary' }} />{selectedOpp?.location}</Typography>
                <Typography variant="body2"><AttachMoney sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5, color: 'text.secondary' }} />{selectedOpp?.compensation}</Typography>
                <Typography variant="body2"><School sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5, color: 'text.secondary' }} />Min CGPA: {selectedOpp?.minCgpa}</Typography>
              </Stack>
            </Grid>

            {/* Match Score */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                <BarChart sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                Your Match Analysis
              </Typography>
              {matchResult ? (
                <>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <Box
                      sx={{
                        width: 72, height: 72, borderRadius: '50%', flexShrink: 0,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: `conic-gradient(${scoreColor(matchResult.score)} ${matchResult.score * 3.6}deg, #e0e0e0 0deg)`
                      }}
                    >
                      <Box sx={{ width: 54, height: 54, borderRadius: '50%', bgcolor: 'background.paper', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Typography variant="h6" fontWeight="bold">{matchResult.score?.toFixed(0)}</Typography>
                      </Box>
                    </Box>
                    <Box>
                      <Chip
                        label={matchResult.eligibilityStatus}
                        color={matchResult.eligibilityStatus === 'ELIGIBLE' ? 'success' : 'error'}
                        sx={{ mb: 0.5, display: 'block' }}
                      />
                      <Typography variant="caption" color="text.secondary">{matchResult.engineType}</Typography>
                    </Box>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic', fontSize: '0.75rem' }}>
                    {matchResult.explanation}
                  </Typography>

                  <Typography variant="caption" fontWeight="bold" gutterBottom>Factor Breakdown</Typography>
                  {matchResult.factors?.map((f: any) =>
                    factorBar(f.name, f.rawValue, f.contribution)
                  )}

                  {matchResult.missingSkills?.length > 0 && (
                    <Box mt={2}>
                      <Typography variant="caption" fontWeight="bold" color="error.main">
                        <Warning sx={{ fontSize: 12, verticalAlign: 'middle' }} /> Missing Skills
                      </Typography>
                      <Box mt={0.5} display="flex" flexWrap="wrap" gap={0.5}>
                        {matchResult.missingSkills.map((s: string) => (
                          <Chip key={s} label={s} size="small" color="error" variant="outlined" />
                        ))}
                      </Box>
                    </Box>
                  )}
                </>
              ) : (
                <Box display="flex" justifyContent="center" py={3}>
                  <CircularProgress size={32} />
                </Box>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialog(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<Send />}
            onClick={() => { setDetailDialog(false); setApplyDialog(true); }}
          >
            Apply Now
          </Button>
        </DialogActions>
      </Dialog>

      {/* Apply Confirmation Dialog */}
      <Dialog open={applyDialog} onClose={() => setApplyDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Confirm Application</DialogTitle>
        <DialogContent>
          <Typography>
            You are about to apply for <strong>"{selectedOpp?.title}"</strong> at <strong>{selectedOpp?.companyName}</strong>.
          </Typography>
          <Alert severity="info" sx={{ mt: 2 }}>
            Your profile, skills, and active resume will be used. You can only apply once per opportunity.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApplyDialog(false)} disabled={applying}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleApply}
            disabled={applying}
            startIcon={applying ? <CircularProgress size={16} /> : <Send />}
          >
            {applying ? 'Submitting...' : 'Submit Application'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PlacementOpportunities;
