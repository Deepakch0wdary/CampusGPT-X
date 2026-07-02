import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
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
  Print as PrintIcon,
  VerifiedUser as VerifiedIcon
} from '@mui/icons-material';

export const ResultDashboard: React.FC = () => {
  const [userRole, setUserRole] = useState<string>('MASTER_ADMIN');
  const [currentTab, setCurrentTab] = useState<'ENTRY' | 'STUDENT' | 'TRANSCRIPT' | 'ANALYTICS' | 'MERIT' | 'REVAL'>('ENTRY');

  // Stats Counters
  const [statistics] = useState({
    passPercentage: 92.4,
    transcriptsGenerated: 48,
    pendingRevaluations: 3,
    topCgpa: 9.92
  });

  // Master lists
  const [results, setResults] = useState<any[]>([
    {
      id: 'res-1',
      studentName: 'Deepak Chowdary',
      rollNo: 'CS2026-01',
      subjectName: 'Advanced Databases',
      internal: 18,
      assignment: 19,
      lab: 9,
      practical: 10,
      project: 15,
      exam: 80,
      grace: 0,
      moderation: 0,
      total: 91,
      grade: 'O',
      point: 10.0,
      status: 'PASS'
    },
    {
      id: 'res-2',
      studentName: 'Alice Smith',
      rollNo: 'CS2026-02',
      subjectName: 'Advanced Databases',
      internal: 15,
      assignment: 15,
      lab: 8,
      practical: 8,
      project: 12,
      exam: 70,
      grace: 0,
      moderation: 0,
      total: 78,
      grade: 'A',
      point: 8.0,
      status: 'PASS'
    }
  ]);

  const [merits] = useState<any[]>([
    { rank: 1, name: 'Deepak Chowdary', rollNo: 'CS2026-01', sgpa: 9.85, cgpa: 9.85, eligible: true },
    { rank: 2, name: 'Alice Smith', rollNo: 'CS2026-02', sgpa: 8.92, cgpa: 8.92, eligible: false },
    { rank: 3, name: 'Bob Johnson', rollNo: 'CS2026-03', sgpa: 8.45, cgpa: 8.45, eligible: false }
  ]);

  const [revals, setRevals] = useState<any[]>([
    { id: 'rev-1', studentName: 'Alice Smith', subjectName: 'Advanced Databases', type: 'REVALUATION', original: 78, status: 'PENDING', remarks: 'Expect re-calculation of final answer sheet.' }
  ]);

  // UI state feedback
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form states
  const [studentRoll, setStudentRoll] = useState<string>('CS2026-01');
  const [subjectId, setSubjectId] = useState<string>('Advanced Databases');
  const [internalVal, setInternalVal] = useState<number>(18);
  const [assignmentVal, setAssignmentVal] = useState<number>(19);
  const [examVal, setExamVal] = useState<number>(80);
  const [graceVal, setGraceVal] = useState<number>(0);

  const [revalOpen, setRevalOpen] = useState<boolean>(false);
  const [selectedReval, setSelectedReval] = useState<any>(null);
  const [reviewMarks, setReviewMarks] = useState<number>(85);

  const handleAddMarks = () => {
    const total = internalVal + assignmentVal + examVal + graceVal;
    let grade = 'F';
    let point = 0.0;
    if (total >= 90) { grade = 'O'; point = 10.0; }
    else if (total >= 80) { grade = 'A+'; point = 9.0; }
    else if (total >= 70) { grade = 'A'; point = 8.0; }
    else if (total >= 60) { grade = 'B'; point = 7.0; }
    else if (total >= 40) { grade = 'C'; point = 5.0; }

    const newRes = {
      id: `res-${Date.now()}`,
      studentName: 'Candidate ' + studentRoll,
      rollNo: studentRoll,
      subjectName: subjectId,
      internal: internalVal,
      assignment: assignmentVal,
      lab: 9,
      practical: 9,
      project: 15,
      exam: examVal,
      grace: graceVal,
      moderation: 0,
      total: total,
      grade: grade,
      point: point,
      status: total >= 40 ? 'PASS' : 'FAIL'
    };

    setResults([newRes, ...results]);
    setFeedbackMsg({ type: 'success', text: `Marks registered successfully. Total Score: ${total}` });
  };

  const handleReviewReval = () => {
    if (!selectedReval) return;
    setRevals(revals.map(r => r.id === selectedReval.id ? { ...r, status: 'APPROVED', updated: reviewMarks } : r));
    setRevalOpen(false);
    setFeedbackMsg({ type: 'success', text: 'Revaluation updated successfully.' });
  };

  return (
    <Box sx={{ p: 4 }}>
      {/* Header section with credentials toggle */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary.main">Result Management System</Typography>
          <Typography variant="subtitle1" color="textSecondary">Publish grades, verify consolidated transcripts, track revaluations, and rank merit lists.</Typography>
        </Box>
        <FormControl variant="outlined" size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Role View</InputLabel>
          <Select value={userRole} onChange={(e) => setUserRole(e.target.value)} label="Role View">
            <MenuItem value="MASTER_ADMIN">Master Admin</MenuItem>
            <MenuItem value="TEACHER">Faculty Member</MenuItem>
            <MenuItem value="STUDENT">Student Candidate</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Global Counters Dashboard */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.05)' }}>
            <Typography variant="h4" fontWeight="bold" color="primary.main">{statistics.passPercentage}%</Typography>
            <Typography variant="subtitle2" color="textSecondary">Class Pass Percentage</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.05)' }}>
            <Typography variant="h4" fontWeight="bold" color="success.main">{statistics.transcriptsGenerated}</Typography>
            <Typography variant="subtitle2" color="textSecondary">Transcripts Generated</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.05)' }}>
            <Typography variant="h4" fontWeight="bold" color="error.main">{statistics.pendingRevaluations}</Typography>
            <Typography variant="subtitle2" color="textSecondary">Pending Revaluations</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.05)' }}>
            <Typography variant="h4" fontWeight="bold" color="warning.main">{statistics.topCgpa}</Typography>
            <Typography variant="subtitle2" color="textSecondary">Highest CGPA Record</Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Alert Notices */}
      {feedbackMsg && (
        <Alert severity={feedbackMsg.type} sx={{ mb: 3 }} onClose={() => setFeedbackMsg(null)}>
          {feedbackMsg.text}
        </Alert>
      )}

      {/* Tab Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(_, val) => setCurrentTab(val)} textColor="primary" indicatorColor="primary">
          <Tab value="ENTRY" label="Faculty Mark Entry" />
          <Tab value="STUDENT" label="Student Result Card" />
          <Tab value="TRANSCRIPT" label="Transcript Viewer" />
          <Tab value="ANALYTICS" label="Analytics Dashboard" />
          <Tab value="MERIT" label="Merit List" />
          <Tab value="REVAL" label="Revaluation requests" />
        </Tabs>
      </Box>

      {/* TAB 1: Faculty Mark Entry */}
      {currentTab === 'ENTRY' && (
        <Grid container spacing={3}>
          {userRole !== 'STUDENT' && (
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, borderRadius: 3 }}>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Enter Candidate Grades</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField label="Student Roll Number" fullWidth value={studentRoll} onChange={(e) => setStudentRoll(e.target.value)} />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField label="Subject / Lecture" fullWidth value={subjectId} onChange={(e) => setSubjectId(e.target.value)} />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField label="Internals (Max 20)" type="number" fullWidth value={internalVal} onChange={(e) => setInternalVal(Number(e.target.value))} />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField label="Assignment (Max 20)" type="number" fullWidth value={assignmentVal} onChange={(e) => setAssignmentVal(Number(e.target.value))} />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField label="Semester Exam (Max 100)" type="number" fullWidth value={examVal} onChange={(e) => setExamVal(Number(e.target.value))} />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField label="Grace Marks" type="number" fullWidth value={graceVal} onChange={(e) => setGraceVal(Number(e.target.value))} />
                  </Grid>
                  <Grid item xs={12}>
                    <Button variant="contained" fullWidth onClick={handleAddMarks}>
                      Calculate & Save Result
                    </Button>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          )}

          <Grid item xs={12} md={userRole !== 'STUDENT' ? 8 : 12}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Current Academic Results Compile</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Student</TableCell>
                      <TableCell>Subject</TableCell>
                      <TableCell>Internal</TableCell>
                      <TableCell>Assignment</TableCell>
                      <TableCell>Semester Exam</TableCell>
                      <TableCell>Total Score</TableCell>
                      <TableCell>Grade</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {results.map((res) => (
                      <TableRow key={res.id}>
                        <TableCell sx={{ fontWeight: 'bold' }}>{res.studentName} ({res.rollNo})</TableCell>
                        <TableCell>{res.subjectName}</TableCell>
                        <TableCell>{res.internal}</TableCell>
                        <TableCell>{res.assignment}</TableCell>
                        <TableCell>{res.exam}</TableCell>
                        <TableCell sx={{ fontWeight: 'bold' }}>{res.total}</TableCell>
                        <TableCell><Chip label={res.grade} size="small" color="secondary" /></TableCell>
                        <TableCell>
                          <Chip label={res.status} size="small" color={res.status === 'PASS' ? 'success' : 'error'} />
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

      {/* TAB 2: Student Result Card */}
      {currentTab === 'STUDENT' && (
        <Paper sx={{ p: 4, borderRadius: 4, border: '1px solid #e5e7eb' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Box>
              <Typography variant="h6" fontWeight="bold">Deepak Chowdary (CS2026-01)</Typography>
              <Typography variant="subtitle2" color="textSecondary">Course: B.Tech Computer Science & Engineering</Typography>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="h5" fontWeight="bold" color="primary">CGPA: 9.85</Typography>
              <Typography variant="subtitle2" color="textSecondary">SGPA: 9.85 | Total Credits: 24</Typography>
            </Box>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Subject Code</TableCell>
                  <TableCell>Subject Name</TableCell>
                  <TableCell>Credits</TableCell>
                  <TableCell>Internal Marks</TableCell>
                  <TableCell>Semester Exam</TableCell>
                  <TableCell>Total Marks</TableCell>
                  <TableCell>Grade Mapped</TableCell>
                  <TableCell>Result Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>CS101</TableCell>
                  <TableCell>Advanced Databases</TableCell>
                  <TableCell>4</TableCell>
                  <TableCell>18</TableCell>
                  <TableCell>80</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>91</TableCell>
                  <TableCell><Chip label="O" color="success" size="small" /></TableCell>
                  <TableCell><Chip label="PASS" color="success" size="small" variant="outlined" /></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>CS102</TableCell>
                  <TableCell>Operating Systems</TableCell>
                  <TableCell>4</TableCell>
                  <TableCell>17</TableCell>
                  <TableCell>72</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>89</TableCell>
                  <TableCell><Chip label="A+" color="success" size="small" /></TableCell>
                  <TableCell><Chip label="PASS" color="success" size="small" variant="outlined" /></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 3: Transcript Viewer */}
      {currentTab === 'TRANSCRIPT' && (
        <Paper sx={{ p: 4, borderRadius: 4, border: '2px dashed #10b981', maxWidth: 700, mx: 'auto' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
            <Box>
              <Typography variant="h5" fontWeight="bold">OFFICIAL TRANSCRIPT OF GRADES</Typography>
              <Typography variant="subtitle2" color="textSecondary">CAMPUSGPT AUTONOMOUS COUNCIL FOR EXAMS</Typography>
            </Box>
            <Chip icon={<VerifiedIcon />} label="Digitally Verified" color="success" />
          </Box>

          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={6}>
              <Typography variant="caption" color="textSecondary">CANDIDATE NAME</Typography>
              <Typography variant="body1" fontWeight="bold">Deepak Chowdary</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="caption" color="textSecondary">ROLL / REGISTER NUMBER</Typography>
              <Typography variant="body1" fontWeight="bold">CS2026-01</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="caption" color="textSecondary">DEGREE / PROGRAM</Typography>
              <Typography variant="body1" fontWeight="bold">Bachelor of Technology (CSE)</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="caption" color="textSecondary">CUMULATIVE GPA (CGPA)</Typography>
              <Typography variant="body1" fontWeight="bold" color="primary">9.85 / 10.00</Typography>
            </Grid>
          </Grid>

          <TableContainer sx={{ mb: 4 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Course Code</TableCell>
                  <TableCell>Course Title</TableCell>
                  <TableCell>Credits</TableCell>
                  <TableCell>Grade</TableCell>
                  <TableCell>Points</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>CS101</TableCell>
                  <TableCell>Advanced Databases</TableCell>
                  <TableCell>4</TableCell>
                  <TableCell>O</TableCell>
                  <TableCell>10.0</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>CS102</TableCell>
                  <TableCell>Operating Systems</TableCell>
                  <TableCell>4</TableCell>
                  <TableCell>A+</TableCell>
                  <TableCell>9.0</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ width: 100, height: 100, bgcolor: 'black', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="caption" color="white">QR SECURE</Typography>
            </Box>
            <Button variant="contained" startIcon={<PrintIcon />}>Print Transcript PDF</Button>
          </Box>
        </Paper>
      )}

      {/* TAB 4: Analytics Dashboard */}
      {currentTab === 'ANALYTICS' && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Departmental Pass Ratio Analysis</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Computer Science</span>
                    <strong>94.2% Passed</strong>
                  </Typography>
                  <Box sx={{ width: '100%', height: 8, bgcolor: '#f3f4f6', borderRadius: 4, overflow: 'hidden', mt: 0.5 }}>
                    <Box sx={{ width: '94.2%', height: '100%', bgcolor: '#10b981' }} />
                  </Box>
                </Box>
                <Box>
                  <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Electrical Engineering</span>
                    <strong>88.5% Passed</strong>
                  </Typography>
                  <Box sx={{ width: '100%', height: 8, bgcolor: '#f3f4f6', borderRadius: 4, overflow: 'hidden', mt: 0.5 }}>
                    <Box sx={{ width: '88.5%', height: '100%', bgcolor: '#3b82f6' }} />
                  </Box>
                </Box>
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Failed / Backlog Ratios</Typography>
              <Box sx={{ p: 2, bgcolor: '#fef2f2', borderRadius: 2, textAlign: 'center' }}>
                <Typography variant="h4" fontWeight="bold" color="error.main">5 Candidates</Typography>
                <Typography variant="subtitle2" color="textSecondary">Total backlogs scheduled for next supplementary cycle</Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* TAB 5: Merit List */}
      {currentTab === 'MERIT' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Semester Ranks & Gold Medalist Eligibility</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Rank Position</TableCell>
                  <TableCell>Student Name</TableCell>
                  <TableCell>Roll Number</TableCell>
                  <TableCell>Semester GPA</TableCell>
                  <TableCell>CGPA Mapped</TableCell>
                  <TableCell>Gold Medalist Eligible</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {merits.map((m) => (
                  <TableRow key={m.rank}>
                    <TableCell sx={{ fontWeight: 'bold' }}>#{m.rank}</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>{m.name}</TableCell>
                    <TableCell>{m.rollNo}</TableCell>
                    <TableCell>{m.sgpa}</TableCell>
                    <TableCell>{m.cgpa}</TableCell>
                    <TableCell>
                      <Chip 
                        label={m.eligible ? 'ELIGIBLE' : 'INELIGIBLE'} 
                        color={m.eligible ? 'success' : 'default'} 
                        size="small" 
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 6: Revaluation requests */}
      {currentTab === 'REVAL' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Active Revaluation requests</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student Name</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Original Mark</TableCell>
                  <TableCell>Current Status</TableCell>
                  <TableCell>Remarks</TableCell>
                  {userRole !== 'STUDENT' && <TableCell align="right">Actions</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {revals.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{r.studentName}</TableCell>
                    <TableCell>{r.subjectName}</TableCell>
                    <TableCell><Chip label={r.type} size="small" color="primary" /></TableCell>
                    <TableCell>{r.original}</TableCell>
                    <TableCell>
                      <Chip 
                        label={r.status} 
                        color={r.status === 'APPROVED' ? 'success' : r.status === 'PENDING' ? 'warning' : 'error'} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>{r.remarks}</TableCell>
                    {userRole !== 'STUDENT' && (
                      <TableCell align="right">
                        <Button 
                          size="small" 
                          variant="outlined" 
                          onClick={() => { setSelectedReval(r); setRevalOpen(true); }}
                          disabled={r.status !== 'PENDING'}
                        >
                          Review & Approve
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* DIALOG: Review Revaluation Marks */}
      <Dialog open={revalOpen} onClose={() => setRevalOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Review Revaluation Request</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField 
                label="Updated Marks (Out of 100)" 
                type="number" 
                fullWidth 
                value={reviewMarks} 
                onChange={(e) => setReviewMarks(Number(e.target.value))} 
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRevalOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleReviewReval}>Apply Approved Marks</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ResultDashboard;
