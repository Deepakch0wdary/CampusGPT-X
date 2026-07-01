import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Tabs, 
  Tab, 
  Paper, 
  Button, 
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
  MenuItem, 
  Grid,
  Card,
  CardContent,
  Avatar,
  Divider,
  LinearProgress,
  Alert
} from '@mui/material';
import { 
  Dashboard as DashIcon, 
  Person as PersonIcon, 
  Event as EventIcon, 
  Assignment as AssignIcon, 
  Assessment as GradeIcon, 
  CardMembership as CertIcon, 
  FolderSpecial as DocIcon, 
  NotificationsActive as AlertIcon, 
  Security as LockIcon,
  CloudUpload as UploadIcon
} from '@mui/icons-material';

export const StudentDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [studentData, setStudentData] = useState<any>(null);
  const [widgets, setWidgets] = useState<any>(null);
  
  // Tab Lists
  const [attendance, setAttendance] = useState<any[]>([]);
  const [results, setResults] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [certificates, setCertificates] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  
  // Profile forms
  const [profileForm, setProfileForm] = useState({
    phoneNumber: '',
    address: '',
    parentName: '',
    parentPhone: '',
    emergencyContact: '',
    bloodGroup: ''
  });
  
  // Dialog controls
  const [openCertDialog, setOpenCertDialog] = useState(false);
  const [certType, setCertType] = useState('BONAFIDE');
  const [openSubmitDialog, setOpenSubmitDialog] = useState(false);
  const [submitAssignId, setSubmitAssignId] = useState<string | null>(null);
  const [submitUrl, setSubmitUrl] = useState('');
  
  // Password change
  const [passwords, setPasswords] = useState({ oldPassword: '', newPassword: '', confirmPassword: '' });
  const [pwdAlert, setPwdAlert] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  const fetchDashboard = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success && payload.data) {
          setStudentData(payload.data.student);
          setWidgets(payload.data.widgets);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchProfile = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/profile', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success && payload.data) {
          setProfileForm({
            phoneNumber: payload.data.phoneNumber || '',
            address: payload.data.address || '',
            parentName: payload.data.parentName || '',
            parentPhone: payload.data.parentPhone || '',
            emergencyContact: payload.data.emergencyContact || '',
            bloodGroup: payload.data.bloodGroup || ''
          });
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const updateProfile = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/profile', {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileForm)
      });
      if (res.ok) {
        alert("Emergency profile parameters updated successfully.");
        fetchDashboard();
      } else {
        alert("Failed to update profile parameters.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAttendance = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/attendance', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setAttendance(payload.data.records || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchResults = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/results', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setResults(payload.data.results || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAssignments = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/assignments', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setAssignments(payload.data.assignments || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchCertificates = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/certificates', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setCertificates(payload.data.certificates || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const requestCertificate = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/certificates/request', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ certificateType: certType })
      });
      if (res.ok) {
        setOpenCertDialog(false);
        fetchCertificates();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchDocuments = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/documents', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setDocuments(payload.data.documents || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchNotifications = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/student/notifications', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setNotifications(payload.data.notifications || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const markNotificationRead = async (id: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/student/notifications/${id}/read`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchNotifications();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const submitAssignment = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/student/assignments/${submitAssignId}/submit`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ submissionUrl: submitUrl })
      });
      if (res.ok) {
        setOpenSubmitDialog(false);
        setSubmitUrl('');
        fetchAssignments();
        fetchDashboard();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const changePassword = async () => {
    if (passwords.newPassword !== passwords.confirmPassword) {
      setPwdAlert({ type: 'error', msg: 'Passwords do not match.' });
      return;
    }
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          old_password: passwords.oldPassword,
          new_password: passwords.newPassword
        })
      });
      if (res.ok) {
        setPwdAlert({ type: 'success', msg: 'Password updated successfully.' });
        setPasswords({ oldPassword: '', newPassword: '', confirmPassword: '' });
      } else {
        const payload = await res.json();
        setPwdAlert({ type: 'error', msg: payload.message || 'Failed to update password.' });
      }
    } catch (e) {
      console.error(e);
      setPwdAlert({ type: 'error', msg: 'Internal server error.' });
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchProfile();
    fetchAttendance();
    fetchResults();
    fetchAssignments();
    fetchCertificates();
    fetchDocuments();
    fetchNotifications();
  }, []);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Welcome Card & Date */}
      {studentData && (
        <Card sx={{ 
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', 
          color: '#f8fafc',
          borderRadius: 4, 
          mb: 4,
          boxShadow: '0 10px 25px rgba(0,0,0,0.15)'
        }}>
          <CardContent sx={{ p: 4 }}>
            <Grid container spacing={3} alignItems="center">
              <Grid item>
                <Avatar sx={{ 
                  width: 90, 
                  height: 90, 
                  bgcolor: '#3b82f6', 
                  fontSize: '2.5rem',
                  fontFamily: 'Outfit',
                  boxShadow: '0 4px 10px rgba(59,130,246,0.3)'
                }} src={studentData.avatarUrl}>
                  {studentData.name[0]}
                </Avatar>
              </Grid>
              <Grid item xs>
                <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800, letterSpacing: '-0.5px' }}>
                  Welcome back, {studentData.name}!
                </Typography>
                <Typography variant="subtitle1" sx={{ color: '#94a3b8', mt: 0.5, fontWeight: 500 }}>
                  USN: {studentData.usn || 'N/A'} • {studentData.department} • Semester {studentData.semester} • Section {studentData.section}
                </Typography>
              </Grid>
              <Grid item sx={{ textAlign: 'right' }}>
                <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 600 }}>
                  {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
                </Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', mt: 0.5 }}>
                  Last Checked: Live
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Main Tab System */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': { fontFamily: 'Outfit', fontWeight: 600, fontSize: '0.95rem' }
          }}
        >
          <Tab icon={<DashIcon />} iconPosition="start" label="Dashboard" />
          <Tab icon={<PersonIcon />} iconPosition="start" label="Profile" />
          <Tab icon={<EventIcon />} iconPosition="start" label="Attendance" />
          <Tab icon={<GradeIcon />} iconPosition="start" label="Results" />
          <Tab icon={<AssignIcon />} iconPosition="start" label="Assignments" />
          <Tab icon={<CertIcon />} iconPosition="start" label="Certificates" />
          <Tab icon={<DocIcon />} iconPosition="start" label="Documents" />
          <Tab icon={<AlertIcon />} iconPosition="start" label="Notifications" />
          <Tab icon={<LockIcon />} iconPosition="start" label="Settings" />
        </Tabs>
      </Box>

      {/* TAB PANELS */}
      {/* 0. DASHBOARD SUMMARY */}
      {tabValue === 0 && widgets && (
        <Grid container spacing={3}>
          {/* Quick Metrics */}
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)' }}>
              <Typography variant="subtitle2" color="textSecondary" fontWeight="600">Overall Attendance</Typography>
              <Typography variant="h3" color="primary" sx={{ mt: 1, fontWeight: 800, fontFamily: 'Outfit' }}>
                {widgets.attendancePercentage}%
              </Typography>
              <LinearProgress variant="determinate" value={widgets.attendancePercentage} sx={{ mt: 2, height: 8, borderRadius: 4 }} />
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)' }}>
              <Typography variant="subtitle2" color="textSecondary" fontWeight="600">Current CGPA</Typography>
              <Typography variant="h3" sx={{ mt: 1, fontWeight: 800, fontFamily: 'Outfit', color: '#16a34a' }}>
                {widgets.cgpa}
              </Typography>
              <Typography variant="caption" color="textSecondary">Scale 10.0</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)' }}>
              <Typography variant="subtitle2" color="textSecondary" fontWeight="600">Credits Completed</Typography>
              <Typography variant="h3" sx={{ mt: 1, fontWeight: 800, fontFamily: 'Outfit', color: '#7c3aed' }}>
                {widgets.creditsCompleted}
              </Typography>
              <Typography variant="caption" color="textSecondary">{widgets.creditsRemaining} Credits Remaining</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)' }}>
              <Typography variant="subtitle2" color="textSecondary" fontWeight="600">Pending Assignments</Typography>
              <Typography variant="h3" sx={{ mt: 1, fontWeight: 800, fontFamily: 'Outfit', color: '#ea580c' }}>
                {widgets.pendingAssignmentsCount}
              </Typography>
              <Typography variant="caption" color="textSecondary">Submit before deadline</Typography>
            </Paper>
          </Grid>

          {/* AI Recommendation Widget */}
          <Grid item xs={12}>
            <Alert severity="info" variant="outlined" sx={{ borderRadius: 3, bgcolor: '#f0f9ff' }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>💡 AI Academic Recommendation Advisor</Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {widgets.aiStudyRecommendation}
              </Typography>
            </Alert>
          </Grid>

          {/* Today's Schedule Map */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📅 Today's Timetable</Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', p: 1.5, bgcolor: '#f8fafc', borderRadius: 2 }}>
                  <Typography variant="body2" fontWeight="600">09:00 AM - 10:00 AM</Typography>
                  <Typography variant="body2">Advanced Algorithms (Room 402)</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', p: 1.5, bgcolor: '#f8fafc', borderRadius: 2 }}>
                  <Typography variant="body2" fontWeight="600">10:15 AM - 11:15 AM</Typography>
                  <Typography variant="body2">Database Management Lab (System 12)</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', p: 1.5, bgcolor: '#f8fafc', borderRadius: 2 }}>
                  <Typography variant="body2" fontWeight="600">11:30 AM - 12:30 PM</Typography>
                  <Typography variant="body2">Software Engineering Lecture (Hall C)</Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>

          {/* Bulletins notices */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📢 Latest Campus Announcements</Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="subtitle2" fontWeight="600">Semester Exam Dates Announced</Typography>
                  <Typography variant="body2" color="textSecondary">Theory examinations will begin from July 15, 2026. Hall tickets available next week.</Typography>
                </Box>
                <Divider />
                <Box>
                  <Typography variant="subtitle2" fontWeight="600">Placement Drive: Google Inc.</Typography>
                  <Typography variant="body2" color="textSecondary">Google recruitment portal is open for Software Engineer Intern profiles. Apply before July 5.</Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* 1. STUDENT PROFILE */}
      {tabValue === 1 && (
        <Paper sx={{ p: 4, borderRadius: 3 }}>
          <Typography variant="h5" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 3 }}>👤 Student Profile Details</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Phone Number" 
                fullWidth 
                value={profileForm.phoneNumber} 
                onChange={(e) => setProfileForm({ ...profileForm, phoneNumber: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Blood Group" 
                fullWidth 
                value={profileForm.bloodGroup} 
                onChange={(e) => setProfileForm({ ...profileForm, bloodGroup: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Parent Name" 
                fullWidth 
                value={profileForm.parentName} 
                onChange={(e) => setProfileForm({ ...profileForm, parentName: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Parent Phone" 
                fullWidth 
                value={profileForm.parentPhone} 
                onChange={(e) => setProfileForm({ ...profileForm, parentPhone: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12}>
              <TextField 
                label="Emergency Contact Number" 
                fullWidth 
                value={profileForm.emergencyContact} 
                onChange={(e) => setProfileForm({ ...profileForm, emergencyContact: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12}>
              <TextField 
                label="Residential Address" 
                multiline 
                rows={3} 
                fullWidth 
                value={profileForm.address} 
                onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12}>
              <Button variant="contained" color="primary" onClick={updateProfile} sx={{ fontFamily: 'Outfit', fontWeight: 600 }}>
                Save Emergency Updates
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* 2. ATTENDANCE HISTORY */}
      {tabValue === 2 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📊 Subject Wise Attendance Breakdown</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Subject Code</TableCell>
                  <TableCell>Subject Name</TableCell>
                  <TableCell align="center">Attended Classes</TableCell>
                  <TableCell align="center">Total Classes</TableCell>
                  <TableCell align="center">Percentage</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {attendance.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell sx={{ fontWeight: '600' }}>{row.subjectCode}</TableCell>
                    <TableCell>{row.subjectName}</TableCell>
                    <TableCell align="center">{row.presentClasses}</TableCell>
                    <TableCell align="center">{row.totalClasses}</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>
                      {row.percentage}%
                    </TableCell>
                    <TableCell>
                      {row.percentage >= 75 ? (
                        <Alert severity="success" sx={{ py: 0, px: 1 }}>Safe</Alert>
                      ) : (
                        <Alert severity="error" sx={{ py: 0, px: 1 }}>Shortage</Alert>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {attendance.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">No attendance details registered.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 3. RESULTS SHEET */}
      {tabValue === 3 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📝 Academic Marks & Grades</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Subject Code</TableCell>
                  <TableCell>Subject Name</TableCell>
                  <TableCell align="center">Internal Marks (IA)</TableCell>
                  <TableCell align="center">External Marks (SEE)</TableCell>
                  <TableCell align="center">Credit Weight</TableCell>
                  <TableCell align="center">Grade</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {results.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.subjectCode}</TableCell>
                    <TableCell>{row.subjectName}</TableCell>
                    <TableCell align="center">{row.internalMarks}</TableCell>
                    <TableCell align="center">{row.externalMarks}</TableCell>
                    <TableCell align="center">{row.credits}</TableCell>
                    <TableCell align="center" sx={{ fontWeight: '700' }}>{row.grade}</TableCell>
                  </TableRow>
                ))}
                {results.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">No exam results recorded.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 4. ASSIGNMENTS VIEW */}
      {tabValue === 4 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📝 Assignments & Submissions</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Subject</TableCell>
                  <TableCell>Assignment Title</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Grade</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {assignments.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.subjectName}</TableCell>
                    <TableCell>{row.title}</TableCell>
                    <TableCell>{new Date(row.dueDate).toLocaleDateString()}</TableCell>
                    <TableCell>
                      {row.submissionStatus === 'PENDING' && (
                        <Alert severity="warning" sx={{ py: 0, px: 1 }}>Pending</Alert>
                      )}
                      {row.submissionStatus === 'SUBMITTED' && (
                        <Alert severity="success" sx={{ py: 0, px: 1 }}>Submitted</Alert>
                      )}
                      {row.submissionStatus === 'LATE' && (
                        <Alert severity="error" sx={{ py: 0, px: 1 }}>Late Submission</Alert>
                      )}
                    </TableCell>
                    <TableCell>{row.grade || 'Not Graded'}</TableCell>
                    <TableCell align="right">
                      {row.submissionStatus === 'PENDING' ? (
                        <Button 
                          variant="contained" 
                          size="small" 
                          startIcon={<UploadIcon />}
                          onClick={() => {
                            setSubmitAssignId(row.id);
                            setOpenSubmitDialog(true);
                          }}
                        >
                          Submit
                        </Button>
                      ) : (
                        <Button variant="outlined" size="small" href={row.submissionUrl} target="_blank">
                          View Submission
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 5. CERTIFICATE REQUESTS */}
      {tabValue === 5 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>📜 Certificate Requests</Typography>
            <Button variant="contained" onClick={() => setOpenCertDialog(true)}>Request Document</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Certificate Type</TableCell>
                  <TableCell>Request Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Download URL</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {certificates.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.certificateType}</TableCell>
                    <TableCell>{new Date(row.requestedAt).toLocaleDateString()}</TableCell>
                    <TableCell>{row.status}</TableCell>
                    <TableCell align="right">
                      {row.documentUrl ? (
                        <Button size="small" variant="outlined" href={row.documentUrl} target="_blank">
                          Download PDF
                        </Button>
                      ) : (
                        <Typography variant="caption" color="textSecondary">Processing...</Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 6. DOCUMENTS */}
      {tabValue === 6 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📁 Digital Documents Repository</Typography>
          <Grid container spacing={3}>
            {documents.map((doc) => (
              <Grid item xs={12} sm={6} md={4} key={doc.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight="700">{doc.name}</Typography>
                    <Typography variant="caption" color="textSecondary">Uploaded: {new Date(doc.uploadedAt).toLocaleDateString()}</Typography>
                    <Box sx={{ mt: 2 }}>
                      <Button variant="contained" size="small" href={doc.documentUrl} target="_blank">
                        Download File
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
            {documents.length === 0 && (
              <Grid item xs={12}>
                <Typography align="center" color="textSecondary">No official documents uploaded yet.</Typography>
              </Grid>
            )}
          </Grid>
        </Paper>
      )}

      {/* 7. NOTIFICATIONS */}
      {tabValue === 7 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>🔔 Broadcast Alerts</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {notifications.map((n) => (
              <Paper 
                key={n.id} 
                variant="outlined" 
                sx={{ 
                  p: 2, 
                  bgcolor: n.read ? '#fff' : '#f0f9ff',
                  borderColor: n.read ? '#e2e8f0' : '#bae6fd'
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2" fontWeight="700">{n.title}</Typography>
                  {!n.read && (
                    <Button size="small" onClick={() => markNotificationRead(n.id)}>Mark Read</Button>
                  )}
                </Box>
                <Typography variant="body2" sx={{ mt: 1 }}>{n.content}</Typography>
                <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1 }}>
                  Sent: {new Date(n.createdAt).toLocaleDateString()}
                </Typography>
              </Paper>
            ))}
            {notifications.length === 0 && (
              <Typography align="center" color="textSecondary">No notifications to display.</Typography>
            )}
          </Box>
        </Paper>
      )}

      {/* 8. SETTINGS */}
      {tabValue === 8 && (
        <Paper sx={{ p: 4, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 3 }}>🔒 Security Settings</Typography>
          {pwdAlert && (
            <Alert severity={pwdAlert.type} sx={{ mb: 2 }}>{pwdAlert.msg}</Alert>
          )}
          <Grid container spacing={3} maxWidth={500}>
            <Grid item xs={12}>
              <TextField 
                label="Old Password" 
                type="password" 
                fullWidth 
                value={passwords.oldPassword} 
                onChange={(e) => setPasswords({ ...passwords, oldPassword: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12}>
              <TextField 
                label="New Password" 
                type="password" 
                fullWidth 
                value={passwords.newPassword} 
                onChange={(e) => setPasswords({ ...passwords, newPassword: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12}>
              <TextField 
                label="Confirm New Password" 
                type="password" 
                fullWidth 
                value={passwords.confirmPassword} 
                onChange={(e) => setPasswords({ ...passwords, confirmPassword: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12}>
              <Button variant="contained" color="primary" onClick={changePassword}>
                Change Password Key
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* MODAL DIALOGS */}
      {/* Cert Request */}
      <Dialog open={openCertDialog} onClose={() => setOpenCertDialog(false)}>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Request Certificate</DialogTitle>
        <DialogContent sx={{ minWidth: 300, mt: 1 }}>
          <TextField 
            select 
            label="Document Type" 
            fullWidth 
            value={certType} 
            onChange={(e) => setCertType(e.target.value)}
          >
            <MenuItem value="BONAFIDE">Bonafide Certificate</MenuItem>
            <MenuItem value="STUDY">Study Status Certificate</MenuItem>
            <MenuItem value="TRANSFER">Transfer Certificate (TC)</MenuItem>
            <MenuItem value="FEE_RECEIPT">Fee Structure Receipt</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCertDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={requestCertificate}>Submit Request</Button>
        </DialogActions>
      </Dialog>

      {/* Assignment Submit */}
      <Dialog open={openSubmitDialog} onClose={() => setOpenSubmitDialog(false)}>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Submit Assignment</DialogTitle>
        <DialogContent sx={{ minWidth: 400, mt: 1 }}>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            Provide the online URL to your submission (e.g. GitHub repo, Google Drive shareable link, or PDF location).
          </Typography>
          <TextField 
            label="Submission Link URL" 
            fullWidth 
            value={submitUrl} 
            onChange={(e) => setSubmitUrl(e.target.value)} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSubmitDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={submitAssignment} disabled={!submitUrl}>Submit Work</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StudentDashboard;
