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
  Alert,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import { 
  Dashboard as DashIcon, 
  Person as PersonIcon, 
  Class as ClassIcon, 
  Assignment as AssignIcon, 
  MenuBook as BookIcon, 
  Quiz as QuizIcon, 
  ExitToApp as LeaveIcon, 
  Notifications as BellIcon, 
  Security as LockIcon
} from '@mui/icons-material';

export const FacultyDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [facultyData, setFacultyData] = useState<any>(null);
  const [widgets, setWidgets] = useState<any>(null);
  const [assignedSubjects, setAssignedSubjects] = useState<any[]>([]);
  
  // Lists
  const [classes, setClasses] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [notes, setNotes] = useState<any[]>([]);
  const [quizzes, setQuizzes] = useState<any[]>([]);
  const [leaves, setLeaves] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  
  // Profile Update Form
  const [profileForm, setProfileForm] = useState({
    officeHours: '',
    qualification: '',
    experience: '',
    researchArea: '',
    specialization: '',
    officeLocation: '',
    emergencyContact: ''
  });
  
  // Sub-dialogs and forms
  const [openRoster, setOpenRoster] = useState(false);
  const [rosterStudents, setRosterStudents] = useState<any[]>([]);
  const [rosterSectionName, setRosterSectionName] = useState('');
  
  const [openAssignDef, setOpenAssignDef] = useState(false);
  const [assignForm, setAssignForm] = useState({ title: '', description: '', dueDate: '', allowResubmission: false, subjectId: '' });
  
  const [openGrading, setOpenGrading] = useState(false);
  const [gradingSubmissions, setGradingSubmissions] = useState<any[]>([]);
  const [gradingAssignId, setGradingAssignId] = useState('');
  const [gradeInput, setGradeInput] = useState({ studentId: '', subjectId: '', internalMarks: 20, externalMarks: 50, grade: 'A', credits: 4 });

  const [openNotes, setOpenNotes] = useState(false);
  const [notesForm, setNotesForm] = useState({ title: '', fileUrl: '', fileType: 'PDF', subjectId: '' });
  
  const [openQuiz, setOpenQuiz] = useState(false);
  const [quizForm, setQuizForm] = useState({ title: '', subjectId: '', questionsJson: '[]', scheduledAt: '' });
  
  const [openLeave, setOpenLeave] = useState(false);
  const [leaveForm, setLeaveForm] = useState({ leaveType: 'CASUAL', startDate: '', endDate: '', reason: '' });
  
  const [openAttend, setOpenAttend] = useState(false);
  const [attendForm, setAttendForm] = useState({ departmentId: '', semesterId: '', sectionId: '', subjectId: '', date: '', period: '1' });
  const [attSessionId, setAttSessionId] = useState<string | null>(null);

  const [passwords, setPasswords] = useState({ oldPassword: '', newPassword: '', confirmPassword: '' });
  const [pwdAlert, setPwdAlert] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  const fetchDashboard = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success && payload.data) {
          setFacultyData(payload.data.faculty);
          setWidgets(payload.data.widgets);
          setAssignedSubjects(payload.data.subjects || []);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchProfile = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/profile', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success && payload.data) {
          setProfileForm({
            officeHours: payload.data.officeHours || '',
            qualification: payload.data.qualification || '',
            experience: payload.data.experience || '',
            researchArea: payload.data.researchArea || '',
            specialization: payload.data.specialization || '',
            officeLocation: payload.data.officeLocation || '',
            emergencyContact: payload.data.emergencyContact || ''
          });
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const saveProfile = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/profile', {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileForm)
      });
      if (res.ok) {
        alert("Faculty profile details updated successfully.");
        fetchDashboard();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchClasses = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/classes', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setClasses(payload.data.classes || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchRoster = async (sectionId: string, sectionName: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/faculty/classes/${sectionId}/students`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setRosterStudents(payload.data.students || []);
        setRosterSectionName(sectionName);
        setOpenRoster(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAssignments = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/assignments', {
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

  const createAssignment = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/assignments', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(assignForm)
      });
      if (res.ok) {
        setOpenAssignDef(false);
        setAssignForm({ title: '', description: '', dueDate: '', allowResubmission: false, subjectId: '' });
        fetchAssignments();
        fetchDashboard();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const deleteAssignment = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this assignment?")) return;
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/faculty/assignments/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchAssignments();
        fetchDashboard();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSubmissions = async (id: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/faculty/assignments/${id}/submissions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setGradingSubmissions(payload.data.submissions || []);
        setGradingAssignId(id);
        setOpenGrading(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const gradeStudent = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/marks/grade', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(gradeInput)
      });
      if (res.ok) {
        alert("Student grade updated successfully.");
        fetchSubmissions(gradingAssignId);
        fetchDashboard();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchNotes = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/notes', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setNotes(payload.data.notes || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const uploadNotes = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/notes', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(notesForm)
      });
      if (res.ok) {
        setOpenNotes(false);
        setNotesForm({ title: '', fileUrl: '', fileType: 'PDF', subjectId: '' });
        fetchNotes();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchQuizzes = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/quizzes', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setQuizzes(payload.data.quizzes || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createQuiz = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/quizzes', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(quizForm)
      });
      if (res.ok) {
        setOpenQuiz(false);
        setQuizForm({ title: '', subjectId: '', questionsJson: '[]', scheduledAt: '' });
        fetchQuizzes();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchLeaves = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/leaves', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setLeaves(payload.data.leaves || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const applyLeave = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/leaves', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(leaveForm)
      });
      if (res.ok) {
        setOpenLeave(false);
        setLeaveForm({ leaveType: 'CASUAL', startDate: '', endDate: '', reason: '' });
        fetchLeaves();
        fetchDashboard();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const prepareAttendance = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/attendance/prepare', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(attendForm)
      });
      if (res.ok) {
        const payload = await res.json();
        setAttSessionId(payload.data.sessionId);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchNotifications = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/faculty/notifications', {
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
    fetchClasses();
    fetchAssignments();
    fetchNotes();
    fetchQuizzes();
    fetchLeaves();
    fetchNotifications();
  }, []);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Welcome Card */}
      {facultyData && (
        <Card sx={{ 
          background: 'linear-gradient(135deg, #1e3a8a 0%, #0d1b3e 100%)', 
          color: '#f8fafc',
          borderRadius: 4, 
          mb: 4,
          boxShadow: '0 8px 20px rgba(13,27,62,0.2)'
        }}>
          <CardContent sx={{ p: 4 }}>
            <Grid container spacing={3} alignItems="center">
              <Grid item>
                <Avatar sx={{ 
                  width: 90, 
                  height: 90, 
                  bgcolor: '#10b981', 
                  fontSize: '2.5rem',
                  fontFamily: 'Outfit',
                  boxShadow: '0 4px 10px rgba(16,185,129,0.3)'
                }}>
                  {facultyData.name[0]}
                </Avatar>
              </Grid>
              <Grid item xs>
                <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800 }}>
                  Welcome back, Professor {facultyData.name}!
                </Typography>
                <Typography variant="subtitle1" sx={{ color: '#94a3b8', mt: 0.5, fontWeight: 500 }}>
                  ID: {facultyData.employeeId} • Department of {facultyData.department} • {facultyData.designation}
                </Typography>
              </Grid>
              <Grid item sx={{ textAlign: 'right' }}>
                <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 600 }}>
                  Faculty Portal
                </Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', mt: 0.5 }}>
                  Term Status: Active
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
          <Tab icon={<ClassIcon />} iconPosition="start" label="My Classes" />
          <Tab icon={<AssignIcon />} iconPosition="start" label="Assignments" />
          <Tab icon={<BookIcon />} iconPosition="start" label="Lesson Notes" />
          <Tab icon={<QuizIcon />} iconPosition="start" label="Quizzes" />
          <Tab icon={<LeaveIcon />} iconPosition="start" label="Leaves" />
          <Tab icon={<BellIcon />} iconPosition="start" label="Notifications" />
          <Tab icon={<LockIcon />} iconPosition="start" label="Settings" />
        </Tabs>
      </Box>

      {/* 0. OVERVIEW DASHBOARD */}
      {tabValue === 0 && widgets && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)' }}>
              <Typography variant="subtitle2" color="textSecondary" fontWeight="600">Assigned Subjects</Typography>
              <Typography variant="h3" color="primary" sx={{ mt: 1, fontWeight: 800, fontFamily: 'Outfit' }}>
                {widgets.assignedSubjectsCount}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)' }}>
              <Typography variant="subtitle2" color="textSecondary" fontWeight="600">Sections Taught</Typography>
              <Typography variant="h3" sx={{ mt: 1, fontWeight: 800, fontFamily: 'Outfit', color: '#16a34a' }}>
                {widgets.assignedSectionsCount}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)' }}>
              <Typography variant="subtitle2" color="textSecondary" fontWeight="600">Pending Evaluations</Typography>
              <Typography variant="h3" sx={{ mt: 1, fontWeight: 800, fontFamily: 'Outfit', color: '#ea580c' }}>
                {widgets.pendingEvaluations}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', background: 'linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)' }}>
              <Typography variant="subtitle2" color="textSecondary" fontWeight="600">Leave Balance</Typography>
              <Typography variant="h3" sx={{ mt: 1, fontWeight: 800, fontFamily: 'Outfit', color: '#7c3aed' }}>
                {widgets.leaveBalance} Days
              </Typography>
            </Paper>
          </Grid>

          {/* Quick Actions Panel */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>⚡ Quick Classroom Actions</Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button variant="contained" onClick={() => setOpenAssignDef(true)}>Create Assignment Def</Button>
                <Button variant="contained" color="secondary" onClick={() => setOpenNotes(true)}>Publish Lesson Note</Button>
                <Button variant="contained" color="success" onClick={() => setOpenQuiz(true)}>Schedule Quiz Test</Button>
                <Button variant="contained" color="warning" onClick={() => setOpenAttend(true)}>Prepare Attendance Session</Button>
                <Button variant="outlined" onClick={() => setOpenLeave(true)}>Apply Leave Request</Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* 1. FACULTY PROFILE */}
      {tabValue === 1 && (
        <Paper sx={{ p: 4, borderRadius: 3 }}>
          <Typography variant="h5" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 3 }}>👤 Faculty Profile Details</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Qualification" 
                fullWidth 
                value={profileForm.qualification} 
                onChange={(e) => setProfileForm({ ...profileForm, qualification: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Specialization" 
                fullWidth 
                value={profileForm.specialization} 
                onChange={(e) => setProfileForm({ ...profileForm, specialization: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Office Location" 
                fullWidth 
                value={profileForm.officeLocation} 
                onChange={(e) => setProfileForm({ ...profileForm, officeLocation: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Office Hours" 
                fullWidth 
                value={profileForm.officeHours} 
                onChange={(e) => setProfileForm({ ...profileForm, officeHours: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Research Area" 
                fullWidth 
                value={profileForm.researchArea} 
                onChange={(e) => setProfileForm({ ...profileForm, researchArea: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField 
                label="Years of Experience" 
                fullWidth 
                value={profileForm.experience} 
                onChange={(e) => setProfileForm({ ...profileForm, experience: e.target.value })} 
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
              <Button variant="contained" color="primary" onClick={saveProfile} sx={{ fontFamily: 'Outfit', fontWeight: 600 }}>
                Save Profile Updates
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* 2. MY CLASSES */}
      {tabValue === 2 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>🏫 Assigned Classes & Strength</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Subject Code</TableCell>
                  <TableCell>Subject Name</TableCell>
                  <TableCell>Section</TableCell>
                  <TableCell>Semester</TableCell>
                  <TableCell>Academic Year</TableCell>
                  <TableCell align="center">Class Strength</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {classes.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell sx={{ fontWeight: '600' }}>{c.subjectCode}</TableCell>
                    <TableCell>{c.subjectName}</TableCell>
                    <TableCell>{c.sectionName}</TableCell>
                    <TableCell>Semester {c.semester}</TableCell>
                    <TableCell>{c.academicYear}</TableCell>
                    <TableCell align="center">{c.studentCount} Students</TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="outlined" onClick={() => fetchRoster(c.sectionId, c.sectionName)}>
                        View Student Roster
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 3. ASSIGNMENTS */}
      {tabValue === 3 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>📝 Authorized Assignments</Typography>
            <Button variant="contained" onClick={() => setOpenAssignDef(true)}>New Assignment</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Subject</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell>Resubmission Allowed</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {assignments.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell sx={{ fontWeight: '600' }}>{row.subjectName}</TableCell>
                    <TableCell>{row.title}</TableCell>
                    <TableCell>{new Date(row.dueDate).toLocaleDateString()}</TableCell>
                    <TableCell>{row.allowResubmission ? 'Yes' : 'No'}</TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="contained" color="success" onClick={() => fetchSubmissions(row.id)} sx={{ mr: 1 }}>
                        Submissions & Grading
                      </Button>
                      <Button size="small" variant="outlined" color="error" onClick={() => deleteAssignment(row.id)}>
                        Delete
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 4. LESSON NOTES */}
      {tabValue === 4 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>📚 Classroom Resource Notes</Typography>
            <Button variant="contained" onClick={() => setOpenNotes(true)}>Publish Resource Notes</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Resource Title</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Format</TableCell>
                  <TableCell align="right">Link</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {notes.map((n) => (
                  <TableRow key={n.id}>
                    <TableCell sx={{ fontWeight: '600' }}>{n.title}</TableCell>
                    <TableCell>{n.subjectName}</TableCell>
                    <TableCell>{n.fileType}</TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="outlined" href={n.fileUrl} target="_blank">
                        Open Link
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 5. QUIZZES */}
      {tabValue === 5 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>❓ Authorized Quizzes</Typography>
            <Button variant="contained" onClick={() => setOpenQuiz(true)}>New Quiz</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Quiz Title</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Scheduled At</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {quizzes.map((q) => (
                  <TableRow key={q.id}>
                    <TableCell sx={{ fontWeight: '600' }}>{q.title}</TableCell>
                    <TableCell>{q.subjectName}</TableCell>
                    <TableCell>{q.status}</TableCell>
                    <TableCell>{q.scheduledAt ? new Date(q.scheduledAt).toLocaleString() : 'Not Scheduled'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 6. LEAVES */}
      {tabValue === 6 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>🌴 Leave Application Tracker</Typography>
            <Button variant="contained" onClick={() => setOpenLeave(true)}>Apply Leave</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Leave Type</TableCell>
                  <TableCell>Start Date</TableCell>
                  <TableCell>End Date</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {leaves.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell sx={{ fontWeight: '600' }}>{row.leaveType}</TableCell>
                    <TableCell>{new Date(row.startDate).toLocaleDateString()}</TableCell>
                    <TableCell>{new Date(row.endDate).toLocaleDateString()}</TableCell>
                    <TableCell>{row.reason}</TableCell>
                    <TableCell>
                      {row.status === 'APPROVED' && <Alert severity="success" sx={{ py: 0, px: 1 }}>Approved</Alert>}
                      {row.status === 'PENDING' && <Alert severity="warning" sx={{ py: 0, px: 1 }}>Pending</Alert>}
                      {row.status === 'REJECTED' && <Alert severity="error" sx={{ py: 0, px: 1 }}>Rejected</Alert>}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 7. NOTIFICATIONS */}
      {tabValue === 7 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>🔔 Staff Announcements</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {notifications.map((n) => (
              <Paper 
                key={n.id} 
                variant="outlined" 
                sx={{ 
                  p: 2, 
                  bgcolor: n.read ? '#fff' : '#fef2f2',
                  borderColor: n.read ? '#e2e8f0' : '#fca5a5'
                }}
              >
                <Typography variant="subtitle2" fontWeight="700">{n.title}</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>{n.content}</Typography>
                <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1 }}>
                  Type: {n.type} • Sent: {new Date(n.createdAt).toLocaleDateString()}
                </Typography>
              </Paper>
            ))}
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

      {/* DIALOGS */}
      {/* Roster Dialog */}
      <Dialog open={openRoster} onClose={() => setOpenRoster(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Roster Strength for {rosterSectionName}</DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student Name</TableCell>
                  <TableCell>USN</TableCell>
                  <TableCell>Email</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rosterStudents.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell sx={{ fontWeight: '600' }}>{s.name}</TableCell>
                    <TableCell>{s.usn || 'N/A'}</TableCell>
                    <TableCell>{s.email}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRoster(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Create Assignment Dialog */}
      <Dialog open={openAssignDef} onClose={() => setOpenAssignDef(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Authorized Assignment</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            label="Assignment Title" 
            fullWidth 
            value={assignForm.title} 
            onChange={(e) => setAssignForm({ ...assignForm, title: e.target.value })} 
          />
          <TextField 
            label="Description" 
            multiline 
            rows={2} 
            fullWidth 
            value={assignForm.description} 
            onChange={(e) => setAssignForm({ ...assignForm, description: e.target.value })} 
          />
          <TextField 
            label="Due Date" 
            type="datetime-local" 
            InputLabelProps={{ shrink: true }} 
            fullWidth 
            value={assignForm.dueDate} 
            onChange={(e) => setAssignForm({ ...assignForm, dueDate: e.target.value })} 
          />
          <TextField 
            select 
            label="Assigned Subject" 
            fullWidth 
            value={assignForm.subjectId} 
            onChange={(e) => setAssignForm({ ...assignForm, subjectId: e.target.value })}
          >
            {assignedSubjects.map((s) => (
              <MenuItem key={s.subjectId} value={s.subjectId}>
                {s.subjectName} ({s.sectionName})
              </MenuItem>
            ))}
          </TextField>
          <FormControlLabel 
            control={<Checkbox checked={assignForm.allowResubmission} onChange={(e) => setAssignForm({ ...assignForm, allowResubmission: e.target.checked })} />} 
            label="Allow Resubmission" 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAssignDef(false)}>Cancel</Button>
          <Button variant="contained" onClick={createAssignment} disabled={!assignForm.title || !assignForm.subjectId}>Publish Assignment</Button>
        </DialogActions>
      </Dialog>

      {/* Submissions & Grading Dialog */}
      <Dialog open={openGrading} onClose={() => setOpenGrading(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Grading Desk</DialogTitle>
        <DialogContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={7}>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Student Name</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Link</TableCell>
                      <TableCell>Grade</TableCell>
                      <TableCell>Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {gradingSubmissions.map((s) => (
                      <TableRow key={s.id}>
                        <TableCell sx={{ fontWeight: '600' }}>{s.studentName}</TableCell>
                        <TableCell>{s.submissionStatus}</TableCell>
                        <TableCell>
                          {s.submissionUrl ? (
                            <Button size="small" href={s.submissionUrl} target="_blank">View</Button>
                          ) : 'No Link'}
                        </TableCell>
                        <TableCell>{s.grade || 'Not Graded'}</TableCell>
                        <TableCell>
                          <Button size="small" variant="contained" onClick={() => setGradeInput({ ...gradeInput, studentId: s.id })}>
                            Select
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
            <Grid item xs={12} md={5}>
              <Paper variant="outlined" sx={{ p: 2.5 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 2 }}>Enter Marks Parameters</Typography>
                <TextField 
                  label="Internal Marks (IA)" 
                  type="number" 
                  fullWidth 
                  value={gradeInput.internalMarks} 
                  onChange={(e) => setGradeInput({ ...gradeInput, internalMarks: parseInt(e.target.value) })} 
                  sx={{ mb: 2 }}
                />
                <TextField 
                  label="External Marks (SEE)" 
                  type="number" 
                  fullWidth 
                  value={gradeInput.externalMarks} 
                  onChange={(e) => setGradeInput({ ...gradeInput, externalMarks: parseInt(e.target.value) })} 
                  sx={{ mb: 2 }}
                />
                <TextField 
                  label="Final Grade" 
                  fullWidth 
                  value={gradeInput.grade} 
                  onChange={(e) => setGradeInput({ ...gradeInput, grade: e.target.value })} 
                  sx={{ mb: 2 }}
                />
                <Button variant="contained" fullWidth onClick={gradeStudent} disabled={!gradeInput.studentId}>
                  Submit Grade Card
                </Button>
              </Paper>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenGrading(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Prepare Attendance Dialog */}
      <Dialog open={openAttend} onClose={() => setOpenAttend(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Prepare Attendance Session</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            label="Period Date" 
            type="date" 
            InputLabelProps={{ shrink: true }} 
            fullWidth 
            value={attendForm.date} 
            onChange={(e) => setAttendForm({ ...attendForm, date: e.target.value })} 
          />
          <TextField 
            label="Period Number" 
            fullWidth 
            value={attendForm.period} 
            onChange={(e) => setAttendForm({ ...attendForm, period: e.target.value })} 
          />
          <TextField 
            select 
            label="Assigned Subject" 
            fullWidth 
            value={attendForm.subjectId} 
            onChange={(e) => setAttendForm({ ...attendForm, subjectId: e.target.value })}
          >
            {assignedSubjects.map((s) => (
              <MenuItem key={s.subjectId} value={s.subjectId}>
                {s.subjectName} ({s.sectionName})
              </MenuItem>
            ))}
          </TextField>
          {attSessionId && (
            <Alert severity="success">
              Session Created!<br />
              <strong>ID: {attSessionId}</strong>
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAttend(false)}>Cancel</Button>
          <Button variant="contained" onClick={prepareAttendance}>Generate Session ID</Button>
        </DialogActions>
      </Dialog>

      {/* Upload Notes Dialog */}
      <Dialog open={openNotes} onClose={() => setOpenNotes(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Upload Notes</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            label="Note Title" 
            fullWidth 
            value={notesForm.title} 
            onChange={(e) => setNotesForm({ ...notesForm, title: e.target.value })} 
          />
          <TextField 
            label="File URL Link" 
            fullWidth 
            value={notesForm.fileUrl} 
            onChange={(e) => setNotesForm({ ...notesForm, fileUrl: e.target.value })} 
          />
          <TextField 
            select 
            label="File Type" 
            fullWidth 
            value={notesForm.fileType} 
            onChange={(e) => setNotesForm({ ...notesForm, fileType: e.target.value })}
          >
            <MenuItem value="PDF">PDF Document</MenuItem>
            <MenuItem value="PPT">Powerpoint Slide (PPT)</MenuItem>
            <MenuItem value="DOCX">Word Document</MenuItem>
            <MenuItem value="VIDEO">Video Link</MenuItem>
          </TextField>
          <TextField 
            select 
            label="Subject" 
            fullWidth 
            value={notesForm.subjectId} 
            onChange={(e) => setNotesForm({ ...notesForm, subjectId: e.target.value })}
          >
            {assignedSubjects.map((s) => (
              <MenuItem key={s.subjectId} value={s.subjectId}>
                {s.subjectName} ({s.sectionName})
              </MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenNotes(false)}>Cancel</Button>
          <Button variant="contained" onClick={uploadNotes} disabled={!notesForm.title || !notesForm.subjectId}>Upload File</Button>
        </DialogActions>
      </Dialog>

      {/* Create Quiz Dialog */}
      <Dialog open={openQuiz} onClose={() => setOpenQuiz(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Create Quiz</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            label="Quiz Title" 
            fullWidth 
            value={quizForm.title} 
            onChange={(e) => setQuizForm({ ...quizForm, title: e.target.value })} 
          />
          <TextField 
            label="Questions JSON List" 
            multiline 
            rows={4} 
            fullWidth 
            value={quizForm.questionsJson} 
            onChange={(e) => setQuizForm({ ...quizForm, questionsJson: e.target.value })} 
          />
          <TextField 
            label="Schedule Start Date" 
            type="datetime-local" 
            InputLabelProps={{ shrink: true }} 
            fullWidth 
            value={quizForm.scheduledAt} 
            onChange={(e) => setQuizForm({ ...quizForm, scheduledAt: e.target.value })} 
          />
          <TextField 
            select 
            label="Subject" 
            fullWidth 
            value={quizForm.subjectId} 
            onChange={(e) => setQuizForm({ ...quizForm, subjectId: e.target.value })}
          >
            {assignedSubjects.map((s) => (
              <MenuItem key={s.subjectId} value={s.subjectId}>
                {s.subjectName} ({s.sectionName})
              </MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenQuiz(false)}>Cancel</Button>
          <Button variant="contained" onClick={createQuiz} disabled={!quizForm.title || !quizForm.subjectId}>Publish Quiz</Button>
        </DialogActions>
      </Dialog>

      {/* Apply Leave Dialog */}
      <Dialog open={openLeave} onClose={() => setOpenLeave(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Apply for Leave</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            select 
            label="Leave Type" 
            fullWidth 
            value={leaveForm.leaveType} 
            onChange={(e) => setLeaveForm({ ...leaveForm, leaveType: e.target.value })}
          >
            <MenuItem value="CASUAL">Casual Leave</MenuItem>
            <MenuItem value="SICK">Sick Leave</MenuItem>
            <MenuItem value="EARNED">Earned Leave</MenuItem>
          </TextField>
          <TextField 
            label="Start Date" 
            type="date" 
            InputLabelProps={{ shrink: true }} 
            fullWidth 
            value={leaveForm.startDate} 
            onChange={(e) => setLeaveForm({ ...leaveForm, startDate: e.target.value })} 
          />
          <TextField 
            label="End Date" 
            type="date" 
            InputLabelProps={{ shrink: true }} 
            fullWidth 
            value={leaveForm.endDate} 
            onChange={(e) => setLeaveForm({ ...leaveForm, endDate: e.target.value })} 
          />
          <TextField 
            label="Reason for Leave" 
            multiline 
            rows={2} 
            fullWidth 
            value={leaveForm.reason} 
            onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenLeave(false)}>Cancel</Button>
          <Button variant="contained" onClick={applyLeave} disabled={!leaveForm.reason}>Submit Request</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FacultyDashboard;
