import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Grid,
  Card,
  CardContent,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Avatar
} from '@mui/material';
import { 
  Face as FaceIcon, 
  CameraAlt as CameraIcon, 
  DeleteForever as DeleteIcon,
  Security as AdminIcon,
  CheckCircle as ApproveIcon, 
  Cancel as RejectIcon
} from '@mui/icons-material';

export const FaceRecognitionDashboard: React.FC = () => {
  const [userRole, setUserRole] = useState<string>('STUDENT');
  const [activeTab, setActiveTab] = useState<'REGISTER' | 'ADMIN' | 'PORTAL'>('REGISTER');

  // Registration angles tracking
  const [capturedAngles, setCapturedAngles] = useState<Record<string, string>>({});
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [profileStatus, setProfileStatus] = useState<string>('NONE');

  // Admin management lists
  const [registrations, setRegistrations] = useState<any[]>([]);
  const [statistics, setStatistics] = useState<any>(null);

  // Review Dialog
  const [selectedProfile, setSelectedProfile] = useState<any>(null);
  const [rejectionReason, setRejectionReason] = useState<string>('');

  // Attendance Simulator
  const [sessionId, setSessionId] = useState<string>('');
  const [attendanceFeedback, setAttendanceFeedback] = useState<string>('');

  const angles = ['FRONT', 'LEFT', 'RIGHT', 'UP', 'DOWN'];

  const loadProfileAndRole = async () => {
    const userStr = localStorage.getItem('user');
    const token = localStorage.getItem('access_token');
    if (userStr) {
      const u = JSON.parse(userStr);
      setUserRole(u.role || 'STUDENT');
      if (u.role === 'MASTER_ADMIN') {
        setActiveTab('ADMIN');
      }
    }

    try {
      // Mock lookup for current profile status
      const res = await fetch('/api/v1/face/registrations', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        // find current user profile
        if (userStr) {
          const u = JSON.parse(userStr);
          const currentProfile = payload.data?.find((p: any) => p.userId === u.id);
          if (currentProfile) {
            setProfileStatus(currentProfile.status);
          }
        }
        if (userRole === 'MASTER_ADMIN') {
          setRegistrations(payload.data || []);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadAdminStats = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/face/statistics', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const p = await res.json();
        setStatistics(p.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const captureAngle = (angle: string) => {
    // Generate a simulated 512-dimension float vector for this angle
    const mockEmbedding = Array.from({ length: 512 }, () => Math.random()).map(v => v.toFixed(4));
    setCapturedAngles(prev => ({
      ...prev,
      [angle]: JSON.stringify(mockEmbedding.map(Number))
    }));
  };

  const submitBiometrics = async () => {
    const token = localStorage.getItem('access_token');
    setStatusMessage(null);

    const payloadEmbeddings = Object.entries(capturedAngles).map(([angle, vecJson]) => ({
      angle,
      embeddingJson: vecJson
    }));

    try {
      const res = await fetch('/api/v1/face/register', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ embeddings: payloadEmbeddings })
      });
      const p = await res.json();
      if (res.ok) {
        setStatusMessage({ type: 'success', text: p.message });
        setProfileStatus('PENDING');
        setCapturedAngles({});
      } else {
        setStatusMessage({ type: 'error', text: p.message || "Registration failed." });
      }
    } catch (e) {
      setStatusMessage({ type: 'error', text: "Error submitting biometric values." });
    }
  };

  const reviewProfile = async (status: 'APPROVED' | 'REJECTED') => {
    const token = localStorage.getItem('access_token');
    if (!selectedProfile) return;
    try {
      const res = await fetch(`/api/v1/face/registrations/${selectedProfile.id}/review`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status, rejectionReason: status === 'REJECTED' ? rejectionReason : null })
      });
      if (res.ok) {
        setSelectedProfile(null);
        setRejectionReason('');
        loadProfileAndRole();
        loadAdminStats();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const deleteProfile = async (id: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/face/registrations/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        loadProfileAndRole();
        loadAdminStats();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const verifyAttendance = async () => {
    const token = localStorage.getItem('access_token');
    setAttendanceFeedback('');
    
    // Setup simulated 512-dim request parameters
    const mockEmbedding = Array.from({ length: 512 }, () => 0.1);

    try {
      const res = await fetch('/api/v1/face/attendance', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sessionId,
          queryEmbeddingJson: JSON.stringify(mockEmbedding),
          latitude: 12.9716,
          longitude: 77.5946,
          deviceId: 'device-client-face',
          liveness: { blinkCount: 2, smileDetected: true, headRotationDegrees: 3.5 },
          spoofing: { spoofProbability: 0.01, spoofCategory: 'NONE' }
        })
      });
      const p = await res.json();
      if (res.ok) {
        setAttendanceFeedback("success:" + p.message);
      } else {
        setAttendanceFeedback("error:" + (p.message || "Verification failed."));
      }
    } catch (e) {
      setAttendanceFeedback("error:Connection error verifying biometrics.");
    }
  };

  useEffect(() => {
    loadProfileAndRole();
    if (userRole === 'MASTER_ADMIN') {
      loadAdminStats();
    }
  }, [userRole]);

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Banner */}
      <Card sx={{ 
        background: 'linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)', 
        color: '#f8fafc',
        borderRadius: 4, 
        mb: 4,
        boxShadow: '0 8px 24px rgba(79,70,229,0.25)'
      }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800 }}>
            👤 Biometric Recognition Desk
          </Typography>
          <Typography variant="subtitle1" sx={{ color: '#c7d2fe', mt: 0.5, fontWeight: 500 }}>
            Biometric Multi-Angle Capture Registration, Face Sign-in, and Anti-Spoof Liveness Validators
          </Typography>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ mb: 4, display: 'flex', gap: 1 }}>
        {userRole === 'MASTER_ADMIN' && (
          <Button 
            variant={activeTab === 'ADMIN' ? 'contained' : 'outlined'} 
            onClick={() => setActiveTab('ADMIN')}
          >
            Admin Panel
          </Button>
        )}
        <Button 
          variant={activeTab === 'REGISTER' ? 'contained' : 'outlined'} 
          onClick={() => setActiveTab('REGISTER')}
        >
          Biometric Registration Wizard
        </Button>
        <Button 
          variant={activeTab === 'PORTAL' ? 'contained' : 'outlined'} 
          onClick={() => setActiveTab('PORTAL')}
        >
          Check-in Verification
        </Button>
      </Box>

      {/* Tab 1: Face Registration Wizard */}
      {activeTab === 'REGISTER' && (
        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>🚀 Biometric Capture Wizard</Typography>
              
              {statusMessage && (
                <Alert severity={statusMessage.type} sx={{ mb: 3 }}>
                  {statusMessage.text}
                </Alert>
              )}

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Biometric quality checklist: Capture your face at the following required angles. Reject filters or low illumination bounds.
                </Typography>

                {angles.map((angle) => {
                  const isCaptured = !!capturedAngles[angle];
                  return (
                    <Box key={angle} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2, border: '1px solid #e2e8f0', borderRadius: 2 }}>
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{angle} Face Angle</Typography>
                        <Typography variant="caption" color={isCaptured ? 'success.main' : 'textSecondary'}>
                          {isCaptured ? '✅ Embedding Vector Generated' : '❌ Captures required'}
                        </Typography>
                      </Box>
                      <Button 
                        variant={isCaptured ? 'outlined' : 'contained'} 
                        color={isCaptured ? 'success' : 'primary'}
                        startIcon={<CameraIcon />}
                        onClick={() => captureAngle(angle)}
                      >
                        {isCaptured ? 'Recapture' : 'Capture'}
                      </Button>
                    </Box>
                  );
                })}

                <Button 
                  variant="contained" 
                  size="large" 
                  disabled={Object.keys(capturedAngles).length < 5 || profileStatus === 'APPROVED'}
                  onClick={submitBiometrics}
                  sx={{ mt: 2 }}
                >
                  Submit Face Embeddings
                </Button>
              </Box>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', minHeight: 300, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
              <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 1 }}>Biometrics Profile Details</Typography>
              <Box sx={{ my: 3 }}>
                <Avatar sx={{ width: 90, height: 90, bgcolor: 'indigo.100', mx: 'auto', mb: 2 }}>
                  <FaceIcon sx={{ fontSize: 50, color: 'primary.main' }} />
                </Avatar>
                <Typography variant="subtitle2">Current Enrollment State:</Typography>
                <Box sx={{ mt: 1 }}>
                  {profileStatus === 'APPROVED' && <Alert severity="success">APPROVED: Account secured with face biometrics.</Alert>}
                  {profileStatus === 'PENDING' && <Alert severity="warning">PENDING: Embeddings awaiting administrator review.</Alert>}
                  {profileStatus === 'REJECTED' && <Alert severity="error">REJECTED: Face profile failed validation checks.</Alert>}
                  {profileStatus === 'NONE' && <Alert severity="info">UNENROLLED: Face recognition checks not initialized.</Alert>}
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Tab 2: Admin Panel */}
      {activeTab === 'ADMIN' && (
        <Grid container spacing={4}>
          {statistics && (
            <Grid item xs={12}>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={3}>
                  <Paper sx={{ p: 2, borderRadius: 3, textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight="bold" color="success.main">{statistics.totalRegisteredCount}</Typography>
                    <Typography variant="caption" color="textSecondary">Secured Face Profiles</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Paper sx={{ p: 2, borderRadius: 3, textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight="bold" color="warning.main">{statistics.pendingReviewCount}</Typography>
                    <Typography variant="caption" color="textSecondary">Profiles Pending Approvals</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Paper sx={{ p: 2, borderRadius: 3, textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight="bold" color="error.main">{statistics.failedRecognitionAttempts}</Typography>
                    <Typography variant="caption" color="textSecondary">Verification Failed Triggers</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Paper sx={{ p: 2, borderRadius: 3, textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight="bold" color="secondary.main">{statistics.spoofedLockdownTriggers}</Typography>
                    <Typography variant="caption" color="textSecondary">Anti-Spoof Blocks Logged</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Grid>
          )}

          <Grid item xs={12}>
            <TableContainer component={Paper} sx={{ borderRadius: 3 }}>
              <Table>
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell><strong>Student/Staff Name</strong></TableCell>
                    <TableCell><strong>User ID</strong></TableCell>
                    <TableCell><strong>Registration Date</strong></TableCell>
                    <TableCell><strong>Biometric Status</strong></TableCell>
                    <TableCell align="right"><strong>Review Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {registrations.map((reg) => (
                    <TableRow key={reg.id}>
                      <TableCell>{reg.name}</TableCell>
                      <TableCell>{reg.userId}</TableCell>
                      <TableCell>{new Date(reg.createdAt).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Box sx={{ mt: 1 }}>
                          {reg.status === 'APPROVED' && <Alert severity="success" sx={{ py: 0 }}>Approved</Alert>}
                          {reg.status === 'PENDING' && <Alert severity="warning" sx={{ py: 0 }}>Pending Approval</Alert>}
                          {reg.status === 'REJECTED' && <Alert severity="error" sx={{ py: 0 }}>Rejected</Alert>}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Button 
                          variant="outlined" 
                          size="small" 
                          startIcon={<AdminIcon />} 
                          onClick={() => setSelectedProfile(reg)}
                          sx={{ mr: 1 }}
                        >
                          Review
                        </Button>
                        <Button 
                          variant="contained" 
                          color="error" 
                          size="small" 
                          startIcon={<DeleteIcon />} 
                          onClick={() => deleteProfile(reg.id)}
                        >
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {registrations.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} align="center">No facial registrations available.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>
      )}

      {/* Tab 3: Check-in Portal */}
      {activeTab === 'PORTAL' && (
        <Paper sx={{ p: 4, borderRadius: 3, maxWidth: 600, mx: 'auto' }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>👤 Biometric Attendance Check-in</Typography>
          
          {attendanceFeedback && (
            <Alert severity={attendanceFeedback.startsWith('success') ? 'success' : 'error'} sx={{ mb: 3 }}>
              {attendanceFeedback.substring(attendanceFeedback.indexOf(':') + 1)}
            </Alert>
          )}

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField 
              label="Active Class Attendance Session ID" 
              placeholder="Paste session ID"
              fullWidth 
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
            />

            <Paper variant="outlined" sx={{ p: 3, textAlign: 'center', border: '1px dashed #4f46e5', bgcolor: '#f5f3ff' }}>
              <CameraIcon sx={{ fontSize: 60, color: 'primary.main', mb: 1 }} />
              <Typography variant="subtitle2">Faculty Portal camera simulator feed</Typography>
              <Typography variant="caption" color="textSecondary">Liveness and anti-spoof checks will automatically verify blinking credentials during capture.</Typography>
            </Paper>

            <Button 
              variant="contained" 
              size="large" 
              color="success" 
              onClick={verifyAttendance} 
              disabled={!sessionId}
            >
              Verify Face Attendance
            </Button>
          </Box>
        </Paper>
      )}

      {/* Review Dialog */}
      <Dialog open={!!selectedProfile} onClose={() => setSelectedProfile(null)}>
        <DialogTitle>Review Biometric Application</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Applicant: {selectedProfile?.name} (ID: {selectedProfile?.userId})
          </Typography>
          <TextField 
            label="Rejection Reason (If Rejecting)" 
            fullWidth 
            multiline 
            rows={3} 
            value={rejectionReason} 
            onChange={(e) => setRejectionReason(e.target.value)} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedProfile(null)}>Cancel</Button>
          <Button variant="contained" color="error" startIcon={<RejectIcon />} onClick={() => reviewProfile('REJECTED')}>Reject</Button>
          <Button variant="contained" color="success" startIcon={<ApproveIcon />} onClick={() => reviewProfile('APPROVED')}>Approve</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FaceRecognitionDashboard;
