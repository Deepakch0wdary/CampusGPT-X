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
  Alert,
  Chip,
  LinearProgress,
  RadioGroup,
  FormControlLabel,
  Radio
} from '@mui/material';
import { 
  TrendingDown as DefaulterIcon,
  SwapHoriz as CorrectionIcon,
  Assignment as SessionIcon
} from '@mui/icons-material';

export const AttendanceDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [userRole, setUserRole] = useState<string>('STUDENT');
  
  // Metadata Lists
  const [academicYears, setAcademicYears] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [programs, setPrograms] = useState<any[]>([]);
  const [semesters, setSemesters] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [slots, setSlots] = useState<any[]>([]);
  
  // Sessions & Mark Attendance
  const [sessions, setSessions] = useState<any[]>([]);
  const [openSessionDialog, setOpenSessionDialog] = useState(false);
  const [sessionForm, setSessionForm] = useState({
    academicYearId: '',
    departmentId: '',
    programId: '',
    semesterId: '',
    sectionId: '',
    subjectId: '',
    timeSlotId: '',
    date: ''
  });
  const [activeSession, setActiveSession] = useState<any>(null);
  const [activeRoster, setActiveRoster] = useState<any[]>([]);

  // Corrections
  const [corrections, setCorrections] = useState<any[]>([]);
  const [openCorrectionDialog, setOpenCorrectionDialog] = useState(false);
  const [corrForm, setCorrForm] = useState({ recordId: '', requestedStatus: 'PRESENT', reason: '' });
  const [openReviewDialog, setOpenReviewDialog] = useState(false);
  const [reviewForm, setReviewForm] = useState({ id: '', status: 'APPROVED', comments: '' });

  // Defaulters & Analytics
  const [defaulters, setDefaulters] = useState<any[]>([]);
  const [defaulterFilter, setDefaulterFilter] = useState({ subjectId: '', sectionId: '' });
  
  // Student Schedules & Summaries
  const [studentSummary, setStudentSummary] = useState<any[]>([]);
  const [studentDetailed, setStudentDetailed] = useState<any[]>([]);

  const fetchMetadata = async () => {
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const u = JSON.parse(userStr);
      setUserRole(u.role || 'STUDENT');
    }
    
    try {
      // Academic Years
      const resAy = await fetch('/api/v1/academic-years', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resAy.ok) {
        const payload = await resAy.json();
        setAcademicYears(payload.data || []);
      }
      
      // Departments
      const resDept = await fetch('/api/v1/departments', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resDept.ok) {
        const payload = await resDept.json();
        setDepartments(payload.data || []);
      }

      // Programs
      const resProg = await fetch('/api/v1/programs', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resProg.ok) {
        const payload = await resProg.json();
        setPrograms(payload.data || []);
      }

      // Semesters
      const resSem = await fetch('/api/v1/semesters', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSem.ok) {
        const payload = await resSem.json();
        setSemesters(payload.data || []);
      }

      // Sections
      const resSec = await fetch('/api/v1/sections', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSec.ok) {
        const payload = await resSec.json();
        setSections(payload.data || []);
      }

      // Subjects
      const resSubj = await fetch('/api/v1/subjects', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSubj.ok) {
        const payload = await resSubj.json();
        setSubjects(payload.data || []);
      }

      // Time slots
      const resSlots = await fetch('/api/v1/timetable/slots', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSlots.ok) {
        const payload = await resSlots.json();
        setSlots(payload.data.slots || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSessions = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/attendance/sessions', { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.ok) {
        const payload = await res.json();
        setSessions(payload.data.sessions || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchCorrections = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/attendance/corrections', { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.ok) {
        const payload = await res.json();
        setCorrections(payload.data.requests || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchDefaulters = async () => {
    try {
      const query = new URLSearchParams(defaulterFilter).toString();
      const res = await fetch(`/api/v1/attendance/defaulters?${query}`);
      if (res.ok) {
        const payload = await res.json();
        setDefaulters(payload.data.defaulters || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchStudentData = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/attendance/student/my-attendance', { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.ok) {
        const payload = await res.json();
        setStudentSummary(payload.data.summaries || []);
        setStudentDetailed(payload.data.records || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createSession = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/attendance/session', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...sessionForm,
          timeSlotId: sessionForm.timeSlotId || null
        })
      });
      if (res.ok) {
        const payload = await res.json();
        setOpenSessionDialog(false);
        setSessionForm({
          academicYearId: '',
          departmentId: '',
          programId: '',
          semesterId: '',
          sectionId: '',
          subjectId: '',
          timeSlotId: '',
          date: ''
        });
        loadSessionRoster(payload.data.id);
        fetchSessions();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadSessionRoster = async (sessionId: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/attendance/session/${sessionId}/students`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setActiveSession(payload.data.session);
        setActiveRoster(payload.data.roster || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const updateRosterStatus = (studentId: string, status: string) => {
    setActiveRoster(prev => prev.map(s => s.id === studentId ? { ...s, status } : s));
  };

  const saveRoster = async (finalize: boolean) => {
    const token = localStorage.getItem('access_token');
    if (!activeSession) return;
    try {
      const payload = {
        records: activeRoster.map(s => ({ studentId: s.id, status: s.status })),
        finalize
      };
      const res = await fetch(`/api/v1/attendance/session/${activeSession.id}/records`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        alert(finalize ? "Attendance finalized and closed." : "Draft details saved.");
        setActiveSession(null);
        setActiveRoster([]);
        fetchSessions();
        fetchStudentData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const submitCorrection = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/attendance/corrections', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(corrForm)
      });
      if (res.ok) {
        setOpenCorrectionDialog(false);
        setCorrForm({ recordId: '', requestedStatus: 'PRESENT', reason: '' });
        fetchCorrections();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const submitCorrectionReview = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/attendance/corrections/${reviewForm.id}/review`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: reviewForm.status, comments: reviewForm.comments })
      });
      if (res.ok) {
        setOpenReviewDialog(false);
        setReviewForm({ id: '', status: 'APPROVED', comments: '' });
        fetchCorrections();
        fetchDefaulters();
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchMetadata();
    fetchSessions();
    fetchCorrections();
    fetchDefaulters();
  }, []);

  useEffect(() => {
    if (userRole === 'STUDENT') {
      fetchStudentData();
    }
  }, [userRole]);

  useEffect(() => {
    fetchDefaulters();
  }, [defaulterFilter]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Premium Header Banner */}
      <Card sx={{ 
        background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)', 
        color: '#f8fafc',
        borderRadius: 4, 
        mb: 4,
        boxShadow: '0 8px 24px rgba(3,105,161,0.25)'
      }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800 }}>
            ✔️ Enterprise Attendance Manager
          </Typography>
          <Typography variant="subtitle1" sx={{ color: '#bae6fd', mt: 0.5, fontWeight: 500 }}>
            Roster Session Planners, Automated Defaulter Tracking, and Resolution Desks
          </Typography>
        </CardContent>
      </Card>

      {/* Role Schedules for Student */}
      {userRole === 'STUDENT' && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={7}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📊 Subject-wise Attendance Summaries</Typography>
              {studentSummary.map((sub, idx) => (
                <Box key={idx} sx={{ mb: 2.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="subtitle2" fontWeight="700">{sub.subjectName}</Typography>
                    <Typography variant="body2" color={sub.percentage < 75 ? 'error.main' : 'success.main'} fontWeight="600">
                      {sub.percentage.toFixed(1)}% ({sub.present}/{sub.total})
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={sub.percentage} 
                    color={sub.percentage < 75 ? 'error' : 'success'} 
                    sx={{ height: 8, borderRadius: 4 }} 
                  />
                </Box>
              ))}
              {studentSummary.length === 0 && <Alert severity="info">No summaries logged.</Alert>}
            </Paper>
          </Grid>
          <Grid item xs={12} md={5}>
            <Paper sx={{ p: 3, borderRadius: 3, maxHeight: 400, overflowY: 'auto' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>📅 Historical Session Records</Typography>
                <Button variant="outlined" size="small" onClick={() => setOpenCorrectionDialog(true)}>Request Correction</Button>
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    {studentDetailed.map((row, idx) => (
                      <TableRow key={idx}>
                        <TableCell sx={{ fontWeight: '600' }}>{new Date(row.date).toLocaleDateString()}</TableCell>
                        <TableCell>{row.subjectName}</TableCell>
                        <TableCell>
                          <Chip 
                            label={row.status} 
                            size="small" 
                            color={row.status === 'PRESENT' ? 'success' : row.status === 'ABSENT' ? 'error' : 'warning'} 
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Admin / Teacher Hub Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ '& .MuiTab-root': { fontFamily: 'Outfit', fontWeight: 600 } }}>
          <Tab icon={<SessionIcon />} iconPosition="start" label="Sessions Hub" />
          <Tab icon={<DefaulterIcon />} iconPosition="start" label="Defaulter Console" />
          <Tab icon={<CorrectionIcon />} iconPosition="start" label="Correction Center" />
        </Tabs>
      </Box>

      {/* 0. ATTENDANCE SESSIONS HUB */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>📂 Active Sessions</Typography>
                {userRole !== 'STUDENT' && (
                  <Button variant="contained" size="small" onClick={() => setOpenSessionDialog(true)}>Log Session</Button>
                )}
              </Box>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {sessions.map((s) => (
                  <Paper 
                    key={s.id} 
                    variant="outlined" 
                    sx={{ 
                      p: 2, 
                      cursor: 'pointer',
                      borderColor: activeSession?.id === s.id ? 'primary.main' : '#e2e8f0',
                      bgcolor: activeSession?.id === s.id ? '#f0f9ff' : '#fff'
                    }}
                    onClick={() => loadSessionRoster(s.id)}
                  >
                    <Typography variant="subtitle2" fontWeight="700">{s.subject}</Typography>
                    <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 0.5 }}>
                      Date: {new Date(s.date).toLocaleDateString()} • Section: {s.section}
                    </Typography>
                    <Chip label={s.status} size="small" color={s.status === 'CLOSED' ? 'success' : 'warning'} sx={{ mt: 1 }} />
                  </Paper>
                ))}
                {sessions.length === 0 && <Typography variant="body2" color="textSecondary">No active sessions.</Typography>}
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={8}>
            {activeSession ? (
              <Paper sx={{ p: 3, borderRadius: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Box>
                    <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>👥 Section Attendance Roster</Typography>
                    <Typography variant="caption" color="textSecondary">
                      Session Subject: {activeSession.subject} • Date: {new Date(activeSession.date).toLocaleDateString()}
                    </Typography>
                  </Box>
                  {activeSession.status === 'ACTIVE' && (
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button variant="outlined" onClick={() => saveRoster(false)}>Save Draft</Button>
                      <Button variant="contained" onClick={() => saveRoster(true)}>Finalize & Close</Button>
                    </Box>
                  )}
                </Box>
                <TableContainer sx={{ border: '1px solid #e2e8f0', borderRadius: 2 }}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Student Name</TableCell>
                        <TableCell>Email</TableCell>
                        <TableCell align="right">Mark Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {activeRoster.map((student) => (
                        <TableRow key={student.id}>
                          <TableCell sx={{ fontWeight: '700' }}>{student.name}</TableCell>
                          <TableCell>{student.email}</TableCell>
                          <TableCell align="right">
                            {activeSession.status === 'ACTIVE' ? (
                              <RadioGroup 
                                row 
                                value={student.status} 
                                onChange={(e) => updateRosterStatus(student.id, e.target.value)}
                              >
                                <FormControlLabel value="PRESENT" control={<Radio size="small" />} label="P" />
                                <FormControlLabel value="ABSENT" control={<Radio size="small" />} label="A" />
                                <FormControlLabel value="LATE" control={<Radio size="small" />} label="L" />
                                <FormControlLabel value="MEDICAL_LEAVE" control={<Radio size="small" />} label="ML" />
                                <FormControlLabel value="ON_DUTY" control={<Radio size="small" />} label="OD" />
                              </RadioGroup>
                            ) : (
                              <Chip 
                                label={student.status} 
                                size="small" 
                                color={student.status === 'PRESENT' ? 'success' : student.status === 'ABSENT' ? 'error' : 'warning'} 
                              />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            ) : (
              <Paper sx={{ p: 4, borderRadius: 3, textAlign: 'center' }}>
                <Typography color="textSecondary">Select a session roster from the left column to mark students.</Typography>
              </Paper>
            )}
          </Grid>
        </Grid>
      )}

      {/* 1. DEFAULTERS CONSOLE */}
      {tabValue === 1 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <TextField 
              select 
              label="Filter Class Section" 
              sx={{ width: 250 }} 
              value={defaulterFilter.sectionId}
              onChange={(e) => setDefaulterFilter({ ...defaulterFilter, sectionId: e.target.value })}
            >
              <MenuItem value=""><em>All Sections</em></MenuItem>
              {sections.map(s => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
            </TextField>
            <TextField 
              select 
              label="Filter Class Subject" 
              sx={{ width: 250 }} 
              value={defaulterFilter.subjectId}
              onChange={(e) => setDefaulterFilter({ ...defaulterFilter, subjectId: e.target.value })}
            >
              <MenuItem value=""><em>All Subjects</em></MenuItem>
              {subjects.map(s => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
            </TextField>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student Name</TableCell>
                  <TableCell>Section</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Percentage</TableCell>
                  <TableCell>Defaulter Grade</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {defaulters.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell sx={{ fontWeight: '700' }}>{d.studentName}</TableCell>
                    <TableCell>{d.sectionName}</TableCell>
                    <TableCell>{d.subjectName}</TableCell>
                    <TableCell sx={{ fontWeight: '600', color: 'error.main' }}>{d.percentage.toFixed(1)}%</TableCell>
                    <TableCell>
                      <Chip label={d.category} color="error" size="small" />
                    </TableCell>
                  </TableRow>
                ))}
                {defaulters.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} align="center">No students are currently defaulting attendance thresholds.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 2. CORRECTION CENTER */}
      {tabValue === 2 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>🔀 Correction Requests Desk</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Correction Target</TableCell>
                  <TableCell>Approval Status</TableCell>
                  {userRole !== 'STUDENT' && <TableCell align="right">Action</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {corrections.map((req) => (
                  <TableRow key={req.id}>
                    <TableCell sx={{ fontWeight: '700' }}>{req.studentName}</TableCell>
                    <TableCell>{req.date ? new Date(req.date).toLocaleDateString() : 'N/A'}</TableCell>
                    <TableCell>{req.subjectName}</TableCell>
                    <TableCell>{req.reason}</TableCell>
                    <TableCell>Change Status: <strong>{req.requestedStatus}</strong></TableCell>
                    <TableCell>
                      <Chip 
                        label={req.status} 
                        size="small" 
                        color={req.status === 'APPROVED' ? 'success' : req.status === 'REJECTED' ? 'error' : 'warning'} 
                      />
                    </TableCell>
                    {userRole !== 'STUDENT' && (
                      <TableCell align="right">
                        {req.status === 'PENDING' && (
                          <Button 
                            variant="contained" 
                            size="small" 
                            color="primary"
                            onClick={() => {
                              setReviewForm({ id: req.id, status: 'APPROVED', comments: '' });
                              setOpenReviewDialog(true);
                            }}
                          >
                            Review Request
                          </Button>
                        )}
                      </TableCell>
                    )}
                  </TableRow>
                ))}
                {corrections.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">No correction requests found.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* DIALOGS */}
      {/* Create Session Dialog */}
      <Dialog open={openSessionDialog} onClose={() => setOpenSessionDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Log Attendance Session</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            select 
            label="Academic Year" 
            fullWidth 
            value={sessionForm.academicYearId} 
            onChange={(e) => setSessionForm({ ...sessionForm, academicYearId: e.target.value })}
          >
            {academicYears.map((ay) => <MenuItem key={ay.id} value={ay.id}>{ay.name}</MenuItem>)}
          </TextField>
          <TextField 
            select 
            label="Department" 
            fullWidth 
            value={sessionForm.departmentId} 
            onChange={(e) => setSessionForm({ ...sessionForm, departmentId: e.target.value })}
          >
            {departments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
          </TextField>
          <TextField 
            select 
            label="Program" 
            fullWidth 
            value={sessionForm.programId} 
            onChange={(e) => setSessionForm({ ...sessionForm, programId: e.target.value })}
          >
            {programs.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
          </TextField>
          <TextField 
            select 
            label="Semester" 
            fullWidth 
            value={sessionForm.semesterId} 
            onChange={(e) => setSessionForm({ ...sessionForm, semesterId: e.target.value })}
          >
            {semesters.map((sem) => <MenuItem key={sem.id} value={sem.id}>Semester {sem.semesterNumber}</MenuItem>)}
          </TextField>
          <TextField 
            select 
            label="Class Section" 
            fullWidth 
            value={sessionForm.sectionId} 
            onChange={(e) => setSessionForm({ ...sessionForm, sectionId: e.target.value })}
          >
            {sections.map((sec) => <MenuItem key={sec.id} value={sec.id}>{sec.name}</MenuItem>)}
          </TextField>
          <TextField 
            select 
            label="Subject" 
            fullWidth 
            value={sessionForm.subjectId} 
            onChange={(e) => setSessionForm({ ...sessionForm, subjectId: e.target.value })}
          >
            {subjects.map((sub) => <MenuItem key={sub.id} value={sub.id}>{sub.name}</MenuItem>)}
          </TextField>
          <TextField 
            select 
            label="Timetable Slot (Optional)" 
            fullWidth 
            value={sessionForm.timeSlotId} 
            onChange={(e) => setSessionForm({ ...sessionForm, timeSlotId: e.target.value })}
          >
            <MenuItem value=""><em>None</em></MenuItem>
            {slots.map((s) => <MenuItem key={s.id} value={s.id}>{s.name} ({s.startTime} - {s.endTime})</MenuItem>)}
          </TextField>
          <TextField 
            label="Session Date" 
            type="date" 
            InputLabelProps={{ shrink: true }} 
            fullWidth 
            value={sessionForm.date} 
            onChange={(e) => setSessionForm({ ...sessionForm, date: e.target.value })} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSessionDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={createSession} disabled={!sessionForm.sectionId || !sessionForm.subjectId || !sessionForm.date}>Create Session</Button>
        </DialogActions>
      </Dialog>

      {/* Request Correction Dialog */}
      <Dialog open={openCorrectionDialog} onClose={() => setOpenCorrectionDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Request Attendance Correction</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            select 
            label="Select Absent Class Record" 
            fullWidth 
            value={corrForm.recordId} 
            onChange={(e) => setCorrForm({ ...corrForm, recordId: e.target.value })}
          >
            {studentDetailed.map((row) => (
              <MenuItem key={row.recordId} value={row.recordId}>
                {new Date(row.date).toLocaleDateString()} - {row.subjectName} ({row.status})
              </MenuItem>
            ))}
          </TextField>
          <TextField 
            select 
            label="Target Status" 
            fullWidth 
            value={corrForm.requestedStatus} 
            onChange={(e) => setCorrForm({ ...corrForm, requestedStatus: e.target.value })}
          >
            <MenuItem value="PRESENT">Present</MenuItem>
            <MenuItem value="ON_DUTY">On Duty</MenuItem>
            <MenuItem value="MEDICAL_LEAVE">Medical Leave</MenuItem>
          </TextField>
          <TextField 
            label="Rationale / Reason" 
            multiline 
            rows={2} 
            fullWidth 
            value={corrForm.reason} 
            onChange={(e) => setCorrForm({ ...corrForm, reason: e.target.value })} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCorrectionDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={submitCorrection} disabled={!corrForm.recordId || !corrForm.reason}>Submit Request</Button>
        </DialogActions>
      </Dialog>

      {/* Review Correction Request Dialog */}
      <Dialog open={openReviewDialog} onClose={() => setOpenReviewDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Review Correction Request</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            select 
            label="Review Decision" 
            fullWidth 
            value={reviewForm.status} 
            onChange={(e) => setReviewForm({ ...reviewForm, status: e.target.value })}
          >
            <MenuItem value="APPROVED">Approve Correction</MenuItem>
            <MenuItem value="REJECTED">Reject Correction</MenuItem>
          </TextField>
          <TextField 
            label="Remarks / Comments" 
            multiline 
            rows={2} 
            fullWidth 
            value={reviewForm.comments} 
            onChange={(e) => setReviewForm({ ...reviewForm, comments: e.target.value })} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenReviewDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={submitCorrectionReview}>Save Review</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AttendanceDashboard;
