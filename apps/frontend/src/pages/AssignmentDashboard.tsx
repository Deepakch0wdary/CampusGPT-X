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
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Chip,
  Tab,
  Tabs
} from '@mui/material';
import {
  Add as AddIcon,
  FileUpload as UploadIcon,
  Grade as GradeIcon
} from '@mui/icons-material';

export const AssignmentDashboard: React.FC = () => {
  const [userRole, setUserRole] = useState<string>('STUDENT');
  const [currentTab, setCurrentTab] = useState<'LIST' | 'STATS'>('LIST');

  // Master Lists & Filtering
  const [assignments, setAssignments] = useState<any[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [search, setSearch] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [statistics, setStatistics] = useState<any>(null);

  // Detail & Action States
  const [selectedAssignment, setSelectedAssignment] = useState<any>(null);
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [selectedSubmission, setSelectedSubmission] = useState<any>(null);

  // Modals
  const [createOpen, setCreateOpen] = useState<boolean>(false);
  const [submitOpen, setSubmitOpen] = useState<boolean>(false);
  const [gradeOpen, setGradeOpen] = useState<boolean>(false);

  // Forms: Create Assignment
  const [title, setTitle] = useState<string>('');
  const [desc, setDesc] = useState<string>('');
  const [instructions, setInstructions] = useState<string>('');
  const [dueDate, setDueDate] = useState<string>('');
  const [maxMarks, setMaxMarks] = useState<number>(100);
  const [assignType, setAssignType] = useState<string>('HOMEWORK');
  const [allowedTypes, setAllowedTypes] = useState<string>('PDF,ZIP');
  const [maxSize, setMaxSize] = useState<number>(10);
  const [pubStatus, setPubStatus] = useState<string>('PUBLISHED');

  // Context properties for creation
  const [academicYears, setAcademicYears] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [programs, setPrograms] = useState<any[]>([]);
  const [semesters, setSemesters] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);

  const [selectedAY, setSelectedAY] = useState<string>('');
  const [selectedDept, setSelectedDept] = useState<string>('');
  const [selectedProg, setSelectedProg] = useState<string>('');
  const [selectedSem, setSelectedSem] = useState<string>('');
  const [selectedSec, setSelectedSec] = useState<string>('');
  const [selectedSubj, setSelectedSubj] = useState<string>('');

  // Forms: Student Submit
  const [submitFileName, setSubmitFileName] = useState<string>('');
  const [submitFileSizeMb, setSubmitFileSizeMb] = useState<number>(1.2);

  // Forms: Faculty Grade
  const [marksObtained, setMarksObtained] = useState<number>(0);
  const [comments, setComments] = useState<string>('');

  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadRoleAndMetadata = async () => {
    const userStr = localStorage.getItem('user');
    const token = localStorage.getItem('access_token');
    if (userStr) {
      const u = JSON.parse(userStr);
      setUserRole(u.role || 'STUDENT');
    }

    try {
      // Load departments, academic years, etc.
      const resAy = await fetch('/api/v1/academic-years', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resAy.ok) {
        const payload = await resAy.json();
        setAcademicYears(payload.data || []);
      }
      const resDept = await fetch('/api/v1/departments', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resDept.ok) {
        const payload = await resDept.json();
        setDepartments(payload.data || []);
      }
      const resProg = await fetch('/api/v1/programs', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resProg.ok) {
        const payload = await resProg.json();
        setPrograms(payload.data || []);
      }
      const resSem = await fetch('/api/v1/semesters', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSem.ok) {
        const payload = await resSem.json();
        setSemesters(payload.data || []);
      }
      const resSec = await fetch('/api/v1/sections', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSec.ok) {
        const payload = await resSec.json();
        setSections(payload.data || []);
      }
      const resSubj = await fetch('/api/v1/subjects', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSubj.ok) {
        const payload = await resSubj.json();
        setSubjects(payload.data || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadAssignments = async () => {
    const token = localStorage.getItem('access_token');
    try {
      let url = `/api/v1/assignments?page=${page}&limit=10&sortBy=dueDate&order=asc`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (typeFilter) url += `&assignmentType=${typeFilter}`;
      if (statusFilter) url += `&status_filter=${statusFilter}`;

      const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.ok) {
        const payload = await res.json();
        setAssignments(payload.data.assignments || []);
        setTotal(payload.data.total || 0);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadStatistics = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/assignments/statistics/summary', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setStatistics(payload.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateAssignment = async () => {
    const token = localStorage.getItem('access_token');
    setFeedbackMsg(null);

    const payload = {
      academicYearId: selectedAY,
      departmentId: selectedDept,
      programId: selectedProg,
      semesterId: selectedSem,
      sectionId: selectedSec,
      subjectId: selectedSubj,
      assignmentType: assignType,
      title,
      description: desc,
      instructions,
      dueDate: new Date(dueDate).toISOString(),
      maxMarks,
      allowedFileTypes: allowedTypes,
      maxUploadSizeMb: maxSize,
      status: pubStatus
    };

    try {
      const res = await fetch('/api/v1/assignments', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      const p = await res.json();
      if (res.ok) {
        setFeedbackMsg({ type: 'success', text: p.message });
        setCreateOpen(false);
        loadAssignments();
        loadStatistics();
        clearForm();
      } else {
        setFeedbackMsg({ type: 'error', text: p.message || "Failed to create assignment." });
      }
    } catch (e) {
      setFeedbackMsg({ type: 'error', text: "Network error creating assignment." });
    }
  };

  const handleStudentSubmit = async () => {
    const token = localStorage.getItem('access_token');
    setFeedbackMsg(null);

    // Validate size and extensions
    const ext = submitFileName.split('.').pop()?.toUpperCase() || '';
    const allowed = selectedAssignment.allowedFileTypes.split(',').map((t: string) => t.trim().toUpperCase());
    if (!allowed.includes(ext)) {
      setFeedbackMsg({ type: 'error', text: `Disallowed extension. Must be: ${selectedAssignment.allowedFileTypes}` });
      return;
    }

    if (submitFileSizeMb > selectedAssignment.maxUploadSizeMb) {
      setFeedbackMsg({ type: 'error', text: `Size exceeds limit of ${selectedAssignment.maxUploadSizeMb} MB.` });
      return;
    }

    const payload = {
      attachments: [
        {
          fileName: submitFileName,
          fileUrl: `http://localhost:8000/storage/submissions/${submitFileName}`,
          fileSize: Math.round(submitFileSizeMb * 1024 * 1024)
        }
      ]
    };

    try {
      const res = await fetch(`/api/v1/assignments/${selectedAssignment.id}/submit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      const p = await res.json();
      if (res.ok) {
        setFeedbackMsg({ type: 'success', text: p.message });
        setSubmitOpen(false);
        loadAssignments();
        loadStatistics();
        // reload details
        loadAssignmentDetails(selectedAssignment.id);
      } else {
        setFeedbackMsg({ type: 'error', text: p.message || "Submission failed." });
      }
    } catch (e) {
      setFeedbackMsg({ type: 'error', text: "Connection error submitting file." });
    }
  };

  const handleFacultyGrade = async () => {
    const token = localStorage.getItem('access_token');
    setFeedbackMsg(null);

    const payload = {
      marksObtained,
      isPublished: true,
      comments
    };

    try {
      const res = await fetch(`/api/v1/assignments/submissions/${selectedSubmission.id}/grade`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      const p = await res.json();
      if (res.ok) {
        setFeedbackMsg({ type: 'success', text: p.message });
        setGradeOpen(false);
        setSelectedSubmission(null);
        if (selectedAssignment) {
          loadSubmissions(selectedAssignment.id);
        }
      } else {
        setFeedbackMsg({ type: 'error', text: p.message || "Evaluation failed." });
      }
    } catch (e) {
      setFeedbackMsg({ type: 'error', text: "Network error submitting grade." });
    }
  };

  const loadAssignmentDetails = async (id: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/assignments/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setSelectedAssignment(payload.data);
        if (userRole === 'TEACHER' || userRole === 'MASTER_ADMIN') {
          loadSubmissions(id);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadSubmissions = async (id: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/assignments/${id}/submissions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setSubmissions(payload.data || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const clearForm = () => {
    setTitle('');
    setDesc('');
    setInstructions('');
    setDueDate('');
    setMaxMarks(100);
    setAllowedTypes('PDF,ZIP');
    setMaxSize(10);
  };

  useEffect(() => {
    loadRoleAndMetadata();
    loadAssignments();
    loadStatistics();
  }, [page, search, typeFilter, statusFilter]);

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Header Banner */}
      <Card sx={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        color: '#f8fafc',
        borderRadius: 4,
        mb: 4,
        boxShadow: '0 8px 30px rgba(15,23,42,0.3)'
      }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800 }}>
                📂 Assignment Hub
              </Typography>
              <Typography variant="subtitle1" sx={{ color: '#94a3b8', mt: 0.5, fontWeight: 500 }}>
                Enterprise Assignment Publishing, Student Submissions, and Grading Console
              </Typography>
            </Box>
            {userRole !== 'STUDENT' && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setCreateOpen(true)}
                sx={{
                  bgcolor: '#3b82f6',
                  color: '#fff',
                  '&:hover': { bgcolor: '#2563eb' },
                  borderRadius: 2,
                  px: 3,
                  py: 1
                }}
              >
                Create Assignment
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ mb: 4, borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={currentTab} onChange={(_, val) => setCurrentTab(val)} textColor="primary" indicatorColor="primary">
          <Tab value="LIST" label="Assignments List" />
          <Tab value="STATS" label="Dashboard Statistics" />
        </Tabs>
      </Box>

      {feedbackMsg && (
        <Alert severity={feedbackMsg.type} sx={{ mb: 3 }} onClose={() => setFeedbackMsg(null)}>
          {feedbackMsg.text}
        </Alert>
      )}

      {/* Tab 1: Assignments list */}
      {currentTab === 'LIST' && (
        <Grid container spacing={4}>
          <Grid item xs={12} md={selectedAssignment ? 7 : 12}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                Total Found: {total} | Page {page}
              </Typography>
              {/* Search & Filters */}
              <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
                <TextField
                  label="Search assignments..."
                  variant="outlined"
                  size="small"
                  sx={{ flexGrow: 1, minWidth: 200 }}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>Type</InputLabel>
                  <Select value={typeFilter} label="Type" onChange={(e) => setTypeFilter(e.target.value)}>
                    <MenuItem value="">All Types</MenuItem>
                    <MenuItem value="HOMEWORK">Homework</MenuItem>
                    <MenuItem value="PROJECT">Project</MenuItem>
                    <MenuItem value="LAB">Lab</MenuItem>
                    <MenuItem value="EXAM">Exam</MenuItem>
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>Status</InputLabel>
                  <Select value={statusFilter} label="Status" onChange={(e) => setStatusFilter(e.target.value)}>
                    <MenuItem value="">All States</MenuItem>
                    <MenuItem value="PUBLISHED">Published</MenuItem>
                    <MenuItem value="DRAFT">Draft</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              <TableContainer>
                <Table>
                  <TableHead sx={{ bgcolor: '#f8fafc' }}>
                    <TableRow>
                      <TableCell><strong>Title</strong></TableCell>
                      <TableCell><strong>Subject</strong></TableCell>
                      <TableCell><strong>Type</strong></TableCell>
                      <TableCell><strong>Due Date</strong></TableCell>
                      <TableCell><strong>Max Marks</strong></TableCell>
                      {userRole === 'STUDENT' && <TableCell><strong>My Status</strong></TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {assignments.map((item) => (
                      <TableRow
                        key={item.id}
                        hover
                        selected={selectedAssignment?.id === item.id}
                        onClick={() => loadAssignmentDetails(item.id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <TableCell>{item.title}</TableCell>
                        <TableCell>{item.subjectName}</TableCell>
                        <TableCell>
                          <Chip label={item.assignmentType} size="small" color="primary" variant="outlined" />
                        </TableCell>
                        <TableCell>{new Date(item.dueDate).toLocaleString()}</TableCell>
                        <TableCell>{item.maxMarks}</TableCell>
                        {userRole === 'STUDENT' && (
                          <TableCell>
                            <Chip
                              label={item.submissionStatus}
                              size="small"
                              color={item.submissionStatus === 'SUBMITTED' ? 'success' : item.submissionStatus === 'LATE' ? 'warning' : 'default'}
                            />
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                    {assignments.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={userRole === 'STUDENT' ? 6 : 5} align="center">No assignments available.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Button size="small" disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>
                  Previous Page
                </Button>
                <Button size="small" disabled={assignments.length < 10} onClick={() => setPage(p => p + 1)}>
                  Next Page
                </Button>
              </Box>
            </Paper>
          </Grid>

          {/* Details Sidebar panel */}
          {selectedAssignment && (
            <Grid item xs={12} md={5}>
              <Paper sx={{ p: 3, borderRadius: 3, border: '1px solid #e2e8f0' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" fontWeight="bold">{selectedAssignment.title}</Typography>
                  <Button size="small" onClick={() => setSelectedAssignment(null)}>Close</Button>
                </Box>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="subtitle2" color="textSecondary">Description</Typography>
                    <Typography variant="body2">{selectedAssignment.description || 'No description provided.'}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="textSecondary">Instructions</Typography>
                    <Typography variant="body2">{selectedAssignment.instructions || 'Follow submission guidelines.'}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="textSecondary">Due Date</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#dc2626' }}>
                      {new Date(selectedAssignment.dueDate).toLocaleString()}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="textSecondary">Submission Configuration</Typography>
                    <Typography variant="body2">Allowed: <strong>{selectedAssignment.allowedFileTypes}</strong> | Max Size: <strong>{selectedAssignment.maxUploadSizeMb} MB</strong></Typography>
                  </Box>

                  {userRole === 'STUDENT' && (
                    <Box sx={{ mt: 2, p: 2, border: '1px dashed #3b82f6', borderRadius: 2, bgcolor: '#f0f9ff' }}>
                      <Typography variant="subtitle2" fontWeight="bold">My Submission Status</Typography>
                      {selectedAssignment.submission ? (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2">Status: <strong>{selectedAssignment.submission.status}</strong></Typography>
                          <Typography variant="body2">Timestamp: {new Date(selectedAssignment.submission.submittedAt).toLocaleString()}</Typography>
                          {selectedAssignment.submission.grade !== null && (
                            <Box sx={{ mt: 1, p: 1, bgcolor: '#f0fdf4', borderRadius: 1 }}>
                              <Typography variant="body2" color="success.main" fontWeight="bold">Marks: {selectedAssignment.submission.grade} / {selectedAssignment.maxMarks}</Typography>
                              <Typography variant="caption" color="textSecondary">Feedback: {selectedAssignment.submission.feedback}</Typography>
                            </Box>
                          )}
                          <Button size="small" startIcon={<UploadIcon />} onClick={() => setSubmitOpen(true)} sx={{ mt: 1 }}>
                            Resubmit Solution
                          </Button>
                        </Box>
                      ) : (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2" color="textSecondary">No submission uploaded.</Typography>
                          <Button variant="contained" size="small" startIcon={<UploadIcon />} onClick={() => setSubmitOpen(true)} sx={{ mt: 1 }}>
                            Upload Submission
                          </Button>
                        </Box>
                      )}
                    </Box>
                  )}

                  {/* Instructor/Admin submissions table */}
                  {userRole !== 'STUDENT' && (
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>Student Submissions</Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell><strong>Student</strong></TableCell>
                              <TableCell><strong>Status</strong></TableCell>
                              <TableCell><strong>Grade</strong></TableCell>
                              <TableCell align="right"><strong>Action</strong></TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {submissions.map((sub) => (
                              <TableRow key={sub.id}>
                                <TableCell>{sub.studentName}</TableCell>
                                <TableCell>
                                  <Chip label={sub.status} size="small" color={sub.status === 'GRADED' ? 'success' : 'default'} />
                                </TableCell>
                                <TableCell>{sub.grade ? `${sub.grade.marksObtained}` : 'N/A'}</TableCell>
                                <TableCell align="right">
                                  <Button 
                                    size="small" 
                                    startIcon={<GradeIcon />} 
                                    onClick={() => {
                                      setSelectedSubmission(sub);
                                      setGradeOpen(true);
                                    }}
                                  >
                                    Grade
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                            {submissions.length === 0 && (
                              <TableRow>
                                <TableCell colSpan={4} align="center">No student uploads yet.</TableCell>
                              </TableRow>
                            )}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  )}
                </Box>
              </Paper>
            </Grid>
          )}
        </Grid>
      )}

      {/* Tab 2: Dashboard Statistics */}
      {currentTab === 'STATS' && statistics && (
        <Box>
          {userRole === 'TEACHER' ? (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={3}>
                <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="bold" color="primary.main">{statistics.totalCreated}</Typography>
                  <Typography variant="subtitle2" color="textSecondary">Created Assignments</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="bold" color="warning.main">{statistics.pendingEvaluationCount}</Typography>
                  <Typography variant="subtitle2" color="textSecondary">Pending Evaluations</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="bold" color="success.main">{statistics.averageMarks}</Typography>
                  <Typography variant="subtitle2" color="textSecondary">Average Marks Obtained</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="bold" color="error.main">{statistics.lateSubmissionsCount}</Typography>
                  <Typography variant="subtitle2" color="textSecondary">Late Submissions</Typography>
                </Paper>
              </Grid>
            </Grid>
          ) : (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="bold" color="warning.main">{statistics.upcomingDeadlines}</Typography>
                  <Typography variant="subtitle2" color="textSecondary">Upcoming Deadlines</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="bold" color="success.main">{statistics.completedAssignments}</Typography>
                  <Typography variant="subtitle2" color="textSecondary">Completed Assignments</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="bold" color="primary.main">{statistics.pendingAssignments}</Typography>
                  <Typography variant="subtitle2" color="textSecondary">Pending Assignments</Typography>
                </Paper>
              </Grid>
            </Grid>
          )}

          {/* Architecture overview for plagiarism checks */}
          <Paper sx={{ p: 4, borderRadius: 3, mt: 4, border: '1px solid #f1f5f9', bgcolor: '#f8fafc' }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>🛡️ Future Plagiarism Detection System Design</Typography>
            <Typography variant="body2" color="textSecondary">
              In subsequent developmental sprints, the code and text similarity engines will map attachments to detect collusion using Winnowing similarity report hashes. Secure AI evaluation structures will check submissions against generated reference answers.
            </Typography>
          </Paper>
        </Box>
      )}

      {/* Create Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Academic Assignment</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Academic Year</InputLabel>
                <Select value={selectedAY} onChange={(e) => setSelectedAY(e.target.value)}>
                  {academicYears.map((ay) => <MenuItem key={ay.id} value={ay.id}>{ay.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Department</InputLabel>
                <Select value={selectedDept} onChange={(e) => setSelectedDept(e.target.value)}>
                  {departments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Program</InputLabel>
                <Select value={selectedProg} onChange={(e) => setSelectedProg(e.target.value)}>
                  {programs.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Semester</InputLabel>
                <Select value={selectedSem} onChange={(e) => setSelectedSem(e.target.value)}>
                  {semesters.map((s) => <MenuItem key={s.id} value={s.id}>Semester {s.semesterNumber}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Section</InputLabel>
                <Select value={selectedSec} onChange={(e) => setSelectedSec(e.target.value)}>
                  {sections.map((s) => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Subject</InputLabel>
                <Select value={selectedSubj} onChange={(e) => setSelectedSubj(e.target.value)}>
                  {subjects.map((s) => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField label="Title" fullWidth value={title} onChange={(e) => setTitle(e.target.value)} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Description" fullWidth multiline rows={3} value={desc} onChange={(e) => setDesc(e.target.value)} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Instructions" fullWidth multiline rows={2} value={instructions} onChange={(e) => setInstructions(e.target.value)} />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField 
                label="Due Date" 
                type="datetime-local" 
                fullWidth 
                InputLabelProps={{ shrink: true }}
                value={dueDate} 
                onChange={(e) => setDueDate(e.target.value)} 
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField label="Max Marks" type="number" fullWidth value={maxMarks} onChange={(e) => setMaxMarks(Number(e.target.value))} />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Assignment Type</InputLabel>
                <Select value={assignType} onChange={(e) => setAssignType(e.target.value)}>
                  <MenuItem value="HOMEWORK">Homework</MenuItem>
                  <MenuItem value="PROJECT">Project</MenuItem>
                  <MenuItem value="LAB">Lab</MenuItem>
                  <MenuItem value="EXAM">Exam</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField label="Allowed Types (Comma Sep)" fullWidth value={allowedTypes} onChange={(e) => setAllowedTypes(e.target.value)} />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField label="Max Size (MB)" type="number" fullWidth value={maxSize} onChange={(e) => setMaxSize(Number(e.target.value))} />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select value={pubStatus} onChange={(e) => setPubStatus(e.target.value)}>
                  <MenuItem value="PUBLISHED">Published</MenuItem>
                  <MenuItem value="DRAFT">Draft</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateAssignment}>Publish Assignment</Button>
        </DialogActions>
      </Dialog>

      {/* Student Submit Dialog */}
      <Dialog open={submitOpen} onClose={() => setSubmitOpen(false)}>
        <DialogTitle>Upload Submission</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Allowed formats: {selectedAssignment?.allowedFileTypes} | Limit: {selectedAssignment?.maxUploadSizeMb} MB
          </Typography>
          <TextField 
            label="File Name" 
            fullWidth 
            placeholder="e.g. solution.zip"
            value={submitFileName} 
            onChange={(e) => setSubmitFileName(e.target.value)} 
            sx={{ mb: 2 }}
          />
          <TextField 
            label="File Size (MB)" 
            type="number" 
            fullWidth 
            value={submitFileSizeMb} 
            onChange={(e) => setSubmitFileSizeMb(Number(e.target.value))} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSubmitOpen(false)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleStudentSubmit}>Submit Files</Button>
        </DialogActions>
      </Dialog>

      {/* Grade Dialog */}
      <Dialog open={gradeOpen} onClose={() => setGradeOpen(false)}>
        <DialogTitle>Evaluate Submission</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Max Marks allowed: {selectedAssignment?.maxMarks}
          </Typography>
          <TextField 
            label="Marks Obtained" 
            type="number" 
            fullWidth 
            value={marksObtained} 
            onChange={(e) => setMarksObtained(Number(e.target.value))} 
            sx={{ mb: 2 }}
          />
          <TextField 
            label="Comments / Feedback" 
            fullWidth 
            multiline 
            rows={3} 
            value={comments} 
            onChange={(e) => setComments(e.target.value)} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGradeOpen(false)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleFacultyGrade}>Submit Marks</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AssignmentDashboard;
