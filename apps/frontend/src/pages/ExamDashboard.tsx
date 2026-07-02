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
  Tabs,
  IconButton
} from '@mui/material';
import {
  Add as AddIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon
} from '@mui/icons-material';

export const ExamDashboard: React.FC = () => {
  const [userRole, setUserRole] = useState<string>('MASTER_ADMIN');
  const [currentTab, setCurrentTab] = useState<'LIST' | 'SEATING' | 'DUTIES' | 'QP' | 'STUDENT'>('LIST');

  // Stats Counters
  const [statistics] = useState({
    totalActiveExams: 8,
    completedExams: 12,
    cancelledExams: 1,
    totalHallTickets: 145
  });

  // Master Lists & States
  const [exams, setExams] = useState<any[]>([
    {
      id: 'ex-1',
      examName: 'Advanced Database Systems Mid-Term',
      examType: 'MID',
      examDate: '2026-07-15',
      startTime: '09:30',
      endTime: '12:30',
      durationMinutes: 180,
      maxMarks: 100,
      passingMarks: 40,
      status: 'ACTIVE',
      subjectName: 'Advanced Databases',
      sectionName: 'CS-A',
      roomNumber: 'EB-101',
      invigilatorName: 'Dr. Sarah Connor'
    },
    {
      id: 'ex-2',
      examName: 'Operating Systems Practical Lab',
      examType: 'LAB',
      examDate: '2026-07-16',
      startTime: '13:30',
      endTime: '16:30',
      durationMinutes: 180,
      maxMarks: 50,
      passingMarks: 20,
      status: 'ACTIVE',
      subjectName: 'Operating Systems',
      sectionName: 'CS-B',
      roomNumber: 'Lab-3',
      invigilatorName: 'Dr. John Doe'
    }
  ]);

  // Seating list
  const [seats, setSeats] = useState<any[]>([
    { id: 's-1', studentName: 'Deepak Chowdary', rollNo: 'CS2026-01', block: 'Block A', room: 'EB-101', bench: 1, seat: 'A-1' },
    { id: 's-2', studentName: 'Alice Smith', rollNo: 'CS2026-02', block: 'Block A', room: 'EB-101', bench: 1, seat: 'A-2' }
  ]);

  // Question papers
  const [questionPapers, setQuestionPapers] = useState<any[]>([
    { id: 'qp-1', examName: 'Advanced Database Systems Mid-Term', fileName: 'adv_db_midterm_v2.pdf', version: 2, status: 'PENDING', uploadedBy: 'Dr. Sarah Connor' }
  ]);

  // Feedback Alerts
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Dialog States
  const [createOpen, setCreateOpen] = useState<boolean>(false);
  const [scheduleOpen, setScheduleOpen] = useState<boolean>(false);
  const [seatOpen, setSeatOpen] = useState<boolean>(false);
  const [qpOpen, setQPOpen] = useState<boolean>(false);
  const [selectedExam, setSelectedExam] = useState<any>(null);

  // Form Fields
  const [examName, setExamName] = useState<string>('');
  const [examType, setExamType] = useState<string>('MID');
  const [examDate, setExamDate] = useState<string>('2026-07-15');
  const [startTime, setStartTime] = useState<string>('09:30');
  const [endTime, setEndTime] = useState<string>('12:30');
  const [maxMarks, setMaxMarks] = useState<number>(100);
  const [passingMarks, setPassingMarks] = useState<number>(40);
  const [instructions, setInstructions] = useState<string>('');

  const [selectedRoom, setSelectedRoom] = useState<string>('EB-101');
  const [selectedInvigilator, setSelectedInvigilator] = useState<string>('Dr. Sarah Connor');

  const [studentId, setStudentId] = useState<string>('CS2026-01');
  const [blockName, setBlockName] = useState<string>('Block A');
  const [benchNo, setBenchNo] = useState<number>(1);
  const [seatNo, setSeatNo] = useState<string>('A-1');

  const [qpFile, setQPFile] = useState<string>('db_exam_draft.pdf');

  // Trigger auto allocation
  const handleAutoAllocation = () => {
    setFeedbackMsg({ type: 'success', text: 'Seating Auto-Allocation calculated successfully for all halls!' });
  };

  // Create exam logic
  const handleCreateExam = () => {
    const newExam = {
      id: `ex-${Date.now()}`,
      examName,
      examType,
      examDate,
      startTime,
      endTime,
      durationMinutes: 180,
      maxMarks,
      passingMarks,
      status: 'ACTIVE',
      subjectName: 'Cryptography & Network Security',
      sectionName: 'CS-A',
      roomNumber: 'Unassigned',
      invigilatorName: 'Unassigned'
    };
    setExams([newExam, ...exams]);
    setCreateOpen(false);
    setFeedbackMsg({ type: 'success', text: `Exam '${examName}' created successfully!` });
  };

  // Schedule exam logic
  const handleScheduleExam = () => {
    setExams(exams.map(e => e.id === selectedExam.id ? { ...e, roomNumber: selectedRoom, invigilatorName: selectedInvigilator } : e));
    setScheduleOpen(false);
    setFeedbackMsg({ type: 'success', text: `Exam scheduled in ${selectedRoom} under ${selectedInvigilator}.` });
  };

  // Seating allocate logic
  const handleAllocateSeat = () => {
    const newSeat = {
      id: `s-${Date.now()}`,
      studentName: 'Candidate ' + studentId,
      rollNo: studentId,
      block: blockName,
      room: selectedRoom,
      bench: benchNo,
      seat: seatNo
    };
    setSeats([...seats, newSeat]);
    setSeatOpen(false);
    setFeedbackMsg({ type: 'success', text: `Seat ${seatNo} allocated successfully.` });
  };

  // Question paper upload
  const handleUploadQP = () => {
    const newQP = {
      id: `qp-${Date.now()}`,
      examName: selectedExam ? selectedExam.examName : 'Cryptography Exam',
      fileName: qpFile,
      version: 1,
      status: 'PENDING',
      uploadedBy: 'Current Faculty'
    };
    setQuestionPapers([newQP, ...questionPapers]);
    setQPOpen(false);
    setFeedbackMsg({ type: 'success', text: `Question paper ${qpFile} uploaded successfully for approval.` });
  };

  // Review QP status
  const handleReviewQP = (id: string, status: 'APPROVED' | 'REJECTED') => {
    setQuestionPapers(questionPapers.map(qp => qp.id === id ? { ...qp, status } : qp));
    setFeedbackMsg({ type: 'success', text: `Question paper review registered as ${status}.` });
  };

  return (
    <Box sx={{ p: 4 }}>
      {/* Header section with credentials toggle */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary.main">Examination Management System</Typography>
          <Typography variant="subtitle1" color="textSecondary">Plan scheduling conflict grids, print student hall tickets, and assign invigilations.</Typography>
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
            <Typography variant="h4" fontWeight="bold" color="primary.main">{statistics.totalActiveExams}</Typography>
            <Typography variant="subtitle2" color="textSecondary">Active Exams Scheduled</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.05)' }}>
            <Typography variant="h4" fontWeight="bold" color="success.main">{statistics.completedExams}</Typography>
            <Typography variant="subtitle2" color="textSecondary">Completed Examinations</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.05)' }}>
            <Typography variant="h4" fontWeight="bold" color="error.main">{statistics.cancelledExams}</Typography>
            <Typography variant="subtitle2" color="textSecondary">Cancelled Schedules</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, borderRadius: 3, textAlign: 'center', boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.05)' }}>
            <Typography variant="h4" fontWeight="bold" color="warning.main">{statistics.totalHallTickets}</Typography>
            <Typography variant="subtitle2" color="textSecondary">Hall Tickets Issued</Typography>
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
          <Tab value="LIST" label="Exams List" />
          <Tab value="SEATING" label="Seating & Rooms" />
          <Tab value="DUTIES" label="Invigilator Duties" />
          <Tab value="QP" label="Question Papers" />
          {userRole === 'STUDENT' && <Tab value="STUDENT" label="My Hall Ticket" />}
        </Tabs>
      </Box>

      {/* TAB 1: Exams List */}
      {currentTab === 'LIST' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3, alignItems: 'center' }}>
            <Typography variant="h6" fontWeight="bold">Active Exam Schedules</Typography>
            {userRole !== 'STUDENT' && (
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
                New Exam Schema
              </Button>
            )}
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Exam Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Slot</TableCell>
                  <TableCell>Room/Lab</TableCell>
                  <TableCell>Invigilator</TableCell>
                  <TableCell>Status</TableCell>
                  {userRole !== 'STUDENT' && <TableCell align="right">Actions</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {exams.map((ex) => (
                  <TableRow key={ex.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{ex.examName}</TableCell>
                    <TableCell><Chip label={ex.examType} size="small" color="secondary" /></TableCell>
                    <TableCell>{ex.examDate}</TableCell>
                    <TableCell>{ex.startTime} - {ex.endTime}</TableCell>
                    <TableCell>{ex.roomNumber}</TableCell>
                    <TableCell>{ex.invigilatorName}</TableCell>
                    <TableCell><Chip label={ex.status} size="small" color="success" /></TableCell>
                    {userRole !== 'STUDENT' && (
                      <TableCell align="right">
                        <Button size="small" variant="outlined" onClick={() => { setSelectedExam(ex); setScheduleOpen(true); }} sx={{ mr: 1 }}>
                          Schedule
                        </Button>
                        <Button size="small" color="primary" onClick={() => { setSelectedExam(ex); setQPOpen(true); }}>
                          QP Link
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

      {/* TAB 2: Seating & Rooms */}
      {currentTab === 'SEATING' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3, alignItems: 'center' }}>
            <Typography variant="h6" fontWeight="bold">Seat Allocation Registry</Typography>
            {userRole !== 'STUDENT' && (
              <Box>
                <Button variant="outlined" color="primary" onClick={handleAutoAllocation} sx={{ mr: 2 }}>
                  Auto Allocate Seats
                </Button>
                <Button variant="contained" startIcon={<AddIcon />} onClick={() => setSeatOpen(true)}>
                  Manual Assign
                </Button>
              </Box>
            )}
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student Name</TableCell>
                  <TableCell>Roll Number</TableCell>
                  <TableCell>Block</TableCell>
                  <TableCell>Room</TableCell>
                  <TableCell>Bench Number</TableCell>
                  <TableCell>Seat Designation</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {seats.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell>{s.studentName}</TableCell>
                    <TableCell>{s.rollNo}</TableCell>
                    <TableCell>{s.block}</TableCell>
                    <TableCell>{s.room}</TableCell>
                    <TableCell>{s.bench}</TableCell>
                    <TableCell><Chip label={s.seat} size="small" color="primary" variant="outlined" /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 3: Duties */}
      {currentTab === 'DUTIES' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>Assigned Invigilator Duties</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Exam Date</TableCell>
                  <TableCell>Duty Shift</TableCell>
                  <TableCell>Assigned Room</TableCell>
                  <TableCell>Duty Faculty</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>2026-07-15</TableCell>
                  <TableCell>MORNING (09:30 - 12:30)</TableCell>
                  <TableCell>EB-101</TableCell>
                  <TableCell>Dr. Sarah Connor</TableCell>
                  <TableCell><Chip label="Assigned" color="warning" size="small" /></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>2026-07-16</TableCell>
                  <TableCell>AFTERNOON (13:30 - 16:30)</TableCell>
                  <TableCell>Lab-3</TableCell>
                  <TableCell>Dr. John Doe</TableCell>
                  <TableCell><Chip label="Completed" color="success" size="small" /></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 4: QP */}
      {currentTab === 'QP' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>Question Paper Repository & Approvals</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Exam Name</TableCell>
                  <TableCell>File Name</TableCell>
                  <TableCell>Version</TableCell>
                  <TableCell>Uploaded By</TableCell>
                  <TableCell>Status</TableCell>
                  {userRole === 'MASTER_ADMIN' && <TableCell align="right">Actions</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {questionPapers.map((qp) => (
                  <TableRow key={qp.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{qp.examName}</TableCell>
                    <TableCell>{qp.fileName}</TableCell>
                    <TableCell>v{qp.version}</TableCell>
                    <TableCell>{qp.uploadedBy}</TableCell>
                    <TableCell>
                      <Chip 
                        label={qp.status} 
                        size="small" 
                        color={qp.status === 'APPROVED' ? 'success' : qp.status === 'REJECTED' ? 'error' : 'default'} 
                      />
                    </TableCell>
                    {userRole === 'MASTER_ADMIN' && (
                      <TableCell align="right">
                        <IconButton color="success" onClick={() => handleReviewQP(qp.id, 'APPROVED')} disabled={qp.status === 'APPROVED'}>
                          <ApproveIcon />
                        </IconButton>
                        <IconButton color="error" onClick={() => handleReviewQP(qp.id, 'REJECTED')} disabled={qp.status === 'REJECTED'}>
                          <RejectIcon />
                        </IconButton>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 5: STUDENT Hall ticket display */}
      {currentTab === 'STUDENT' && (
        <Paper sx={{ p: 4, borderRadius: 4, border: '2px dashed #3b82f6', maxWidth: 600, mx: 'auto', textAlign: 'center' }}>
          <Typography variant="h5" fontWeight="bold" sx={{ mb: 1 }}>OFFICIAL ADMIT CARD (HALL TICKET)</Typography>
          <Typography variant="subtitle2" color="textSecondary" sx={{ mb: 3 }}>CAMPUSGPT UNIVERSITY EXAMINATION COUNCIL</Typography>
          
          <Grid container spacing={2} textAlign="left" sx={{ mb: 4 }}>
            <Grid item xs={6}>
              <Typography variant="caption" color="textSecondary">STUDENT NAME</Typography>
              <Typography variant="body1" fontWeight="bold">Deepak Chowdary</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="caption" color="textSecondary">ROLL NUMBER</Typography>
              <Typography variant="body1" fontWeight="bold">CS2026-01</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="caption" color="textSecondary">EXAM CENTER</Typography>
              <Typography variant="body1" fontWeight="bold">Engineering Block Main</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="caption" color="textSecondary">ALLOCATED SEAT</Typography>
              <Typography variant="body1" fontWeight="bold">Bench 1 (A-1)</Typography>
            </Grid>
          </Grid>

          <Box sx={{ bgcolor: '#f3f4f6', p: 2, borderRadius: 2, mb: 4 }}>
            <Typography variant="subtitle2" color="textSecondary" sx={{ mb: 1 }}>VERIFICATION BARCODE / QR REPRESENTATION</Typography>
            <Box sx={{ width: 100, height: 100, bgcolor: 'black', mx: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="caption" color="white">QR DECRYPT</Typography>
            </Box>
          </Box>

          <Button variant="contained" fullWidth>Download Admit PDF</Button>
        </Paper>
      )}

      {/* DIALOG 1: Create Exam */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Examination Schema</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField label="Exam Name" fullWidth value={examName} onChange={(e) => setExamName(e.target.value)} />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Exam Type</InputLabel>
                <Select value={examType} onChange={(e) => setExamType(e.target.value)} label="Exam Type">
                  <MenuItem value="MID">Mid Exams</MenuItem>
                  <MenuItem value="SEMESTER">Semester Exams</MenuItem>
                  <MenuItem value="LAB">Lab Exams</MenuItem>
                  <MenuItem value="SUPPLEMENTARY">Supplementary</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <TextField label="Exam Date" type="date" fullWidth value={examDate} onChange={(e) => setExamDate(e.target.value)} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Start Time" type="time" fullWidth value={startTime} onChange={(e) => setStartTime(e.target.value)} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="End Time" type="time" fullWidth value={endTime} onChange={(e) => setEndTime(e.target.value)} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Maximum Marks" type="number" fullWidth value={maxMarks} onChange={(e) => setMaxMarks(Number(e.target.value))} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Passing Marks" type="number" fullWidth value={passingMarks} onChange={(e) => setPassingMarks(Number(e.target.value))} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Instructions" multiline rows={2} fullWidth value={instructions} onChange={(e) => setInstructions(e.target.value)} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateExam}>Publish Exam</Button>
        </DialogActions>
      </Dialog>

      {/* DIALOG 2: Schedule & Conflict Checks */}
      <Dialog open={scheduleOpen} onClose={() => setScheduleOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Assign Room & Invigilator</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Select Room / Laboratory</InputLabel>
                <Select value={selectedRoom} onChange={(e) => setSelectedRoom(e.target.value)} label="Select Room / Laboratory">
                  <MenuItem value="EB-101">EB-101 (Engineering Block)</MenuItem>
                  <MenuItem value="EB-102">EB-102 (Engineering Block)</MenuItem>
                  <MenuItem value="Lab-3">Lab-3 (CSE Lab)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Assign Invigilator</InputLabel>
                <Select value={selectedInvigilator} onChange={(e) => setSelectedInvigilator(e.target.value)} label="Assign Invigilator">
                  <MenuItem value="Dr. Sarah Connor">Dr. Sarah Connor</MenuItem>
                  <MenuItem value="Dr. John Doe">Dr. John Doe</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScheduleOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleScheduleExam}>Apply Allocation</Button>
        </DialogActions>
      </Dialog>

      {/* DIALOG 3: Manual Seating Allocate */}
      <Dialog open={seatOpen} onClose={() => setSeatOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Allocate Seating Location</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField label="Student Roll Number" fullWidth value={studentId} onChange={(e) => setStudentId(e.target.value)} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Block Name" fullWidth value={blockName} onChange={(e) => setBlockName(e.target.value)} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Bench Number" type="number" fullWidth value={benchNo} onChange={(e) => setBenchNo(Number(e.target.value))} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Seat Designation" fullWidth value={seatNo} onChange={(e) => setSeatNo(e.target.value)} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSeatOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAllocateSeat}>Assign Seat</Button>
        </DialogActions>
      </Dialog>

      {/* DIALOG 4: Question Paper Upload */}
      <Dialog open={qpOpen} onClose={() => setQPOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Link Question Paper Version</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField label="File Name" fullWidth value={qpFile} onChange={(e) => setQPFile(e.target.value)} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQPOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUploadQP}>Submit for Review</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExamDashboard;
