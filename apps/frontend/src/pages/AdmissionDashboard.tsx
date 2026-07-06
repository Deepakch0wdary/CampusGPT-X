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
  Card,
  CardContent,
  IconButton
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Attachment as DocIcon,
  HowToReg as EnrollIcon
} from '@mui/icons-material';

export const AdmissionDashboard: React.FC = () => {
  const [role, setRole] = useState<string>('ADMISSION_OFFICE');
  const [tab, setTab] = useState<'LIST' | 'FORM' | 'VERIFY' | 'ENROLL' | 'ANALYTICS'>('LIST');

  // Master applications list state
  const [applications, setApplications] = useState<any[]>([
    {
      id: 'app-1',
      applicationNumber: 'APP-2026-001',
      applicantName: 'Samantha Cooper',
      email: 'samantha@test.com',
      phone: '9876543210',
      status: 'SUBMITTED',
      quota: 'MERIT',
      category: 'GENERAL',
      entranceScore: 94.5,
      documents: [
        { id: 'doc-1', name: '10th Marks Card.pdf', category: '10th Marks Card', status: 'PENDING' },
        { id: 'doc-2', name: 'EntranceScoreCard.pdf', category: 'Entrance Score Card', status: 'PENDING' }
      ]
    },
    {
      id: 'app-2',
      applicationNumber: 'APP-2026-002',
      applicantName: 'Marcus Vance',
      email: 'marcus@test.com',
      phone: '9988776655',
      status: 'APPROVED',
      quota: 'MANAGEMENT',
      category: 'OBC',
      entranceScore: 82.0,
      documents: [
        { id: 'doc-3', name: '12th Marks Card.pdf', category: '12th Marks Card', status: 'VERIFIED' }
      ]
    }
  ]);

  const [enrollments, setEnrollments] = useState<any[]>([
    { id: 'enr-1', enrollmentNumber: 'ENR-CS-001', studentName: 'Samantha Cooper', usn: 'USN202609A', rollNo: 'ROLL-101', status: 'ACTIVE' }
  ]);

  // Form payload state
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [quota, setQuota] = useState('MERIT');
  const [category, setCategory] = useState('GENERAL');

  // Dialog reviews
  const [reviewOpen, setReviewOpen] = useState(false);
  const [selectedApp, setSelectedApp] = useState<any>(null);
  const [reviewComment, setReviewComment] = useState('');

  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleCreateDraft = () => {
    if (!newName || !newEmail) {
      setFeedback({ type: 'error', text: 'Please fill name and email.' });
      return;
    }
    const newApp = {
      id: `app-${Date.now()}`,
      applicationNumber: `APP-2026-00${applications.length + 1}`,
      applicantName: newName,
      email: newEmail,
      phone: newPhone,
      status: 'DRAFT',
      quota,
      category,
      entranceScore: 85.0,
      documents: []
    };
    setApplications([...applications, newApp]);
    setFeedback({ type: 'success', text: `Draft created successfully: ${newApp.applicationNumber}` });
    setNewName('');
    setNewEmail('');
    setNewPhone('');
    setTab('LIST');
  };

  const handleReviewAction = (status: string) => {
    if (!selectedApp) return;
    setApplications(applications.map(a => a.id === selectedApp.id ? { ...a, status } : a));
    setFeedback({ type: 'success', text: `Application ${selectedApp.applicationNumber} transitioned to ${status}.` });
    setReviewOpen(false);
  };

  const handleVerifyDoc = (appId: string, docId: string, verified: boolean) => {
    setApplications(applications.map(a => {
      if (a.id === appId) {
        return {
          ...a,
          documents: a.documents.map((d: any) => d.id === docId ? { ...d, status: verified ? 'VERIFIED' : 'REJECTED' } : d)
        };
      }
      return a;
    }));
    setFeedback({ type: 'success', text: `Document marked as ${verified ? 'VERIFIED' : 'REJECTED'}.` });
  };

  const handleEnroll = (app: any) => {
    if (app.status !== 'APPROVED') {
      setFeedback({ type: 'error', text: 'Only approved applications can be enrolled.' });
      return;
    }
    const newEnroll = {
      id: `enr-${Date.now()}`,
      enrollmentNumber: `ENR-CS-00${enrollments.length + 1}`,
      studentName: app.applicantName,
      usn: `USN2026${Math.floor(1000 + Math.random() * 9000)}`,
      rollNo: `ROLL-${100 + enrollments.length + 1}`,
      status: 'ACTIVE'
    };
    setEnrollments([...enrollments, newEnroll]);
    setApplications(applications.map(a => a.id === app.id ? { ...a, status: 'ENROLLED' } : a));
    setFeedback({ type: 'success', text: `Successfully enrolled ${app.applicantName}. ID: ${newEnroll.enrollmentNumber}` });
  };

  return (
    <Box sx={{ p: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary">Admission Portal</Typography>
          <Typography variant="subtitle1" color="textSecondary">Manage applicant lifecycles, document verification workflow reviews, and enrollment cards.</Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Role Context</InputLabel>
          <Select value={role} onChange={(e) => setRole(e.target.value)} label="Role Context">
            <MenuItem value="ADMISSION_OFFICE">Admission Officer</MenuItem>
            <MenuItem value="STUDENT">Applicant Student</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {feedback && (
        <Alert severity={feedback.type} sx={{ mb: 3 }} onClose={() => setFeedback(null)}>
          {feedback.text}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tab} onChange={(_, val) => setTab(val)} textColor="primary" indicatorColor="primary">
          <Tab value="LIST" label="Applications Directory" />
          <Tab value="FORM" label="Submit Application" />
          <Tab value="VERIFY" label="Verify Documents" />
          <Tab value="ENROLL" label="Enrollments Console" />
          <Tab value="ANALYTICS" label="Admissions Analytics" />
        </Tabs>
      </Box>

      {/* TAB 1: APPLICATIONS LIST */}
      {tab === 'LIST' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Admission Registries</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>App Number</TableCell>
                  <TableCell>Applicant Name</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Quota</TableCell>
                  <TableCell>Entrance Score</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {applications.map((app) => (
                  <TableRow key={app.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{app.applicationNumber}</TableCell>
                    <TableCell>{app.applicantName}</TableCell>
                    <TableCell>{app.email}</TableCell>
                    <TableCell>{app.quota}</TableCell>
                    <TableCell>{app.entranceScore}%</TableCell>
                    <TableCell>
                      <Chip
                        label={app.status}
                        color={
                          app.status === 'APPROVED' || app.status === 'ENROLLED'
                            ? 'success'
                            : app.status === 'REJECTED'
                            ? 'error'
                            : 'warning'
                        }
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      {role === 'ADMISSION_OFFICE' && app.status === 'SUBMITTED' && (
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => { setSelectedApp(app); setReviewOpen(true); }}
                        >
                          Review & Comment
                        </Button>
                      )}
                      {role === 'ADMISSION_OFFICE' && app.status === 'APPROVED' && (
                        <Button
                          size="small"
                          variant="contained"
                          color="success"
                          startIcon={<EnrollIcon />}
                          onClick={() => handleEnroll(app)}
                        >
                          Enroll Candidate
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

      {/* TAB 2: APPLICATION FORM */}
      {tab === 'FORM' && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 4, borderRadius: 3 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>Apply for Admission</Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField label="Full Name" fullWidth value={newName} onChange={(e) => setNewName(e.target.value)} />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField label="Email Address" type="email" fullWidth value={newEmail} onChange={(e) => setNewEmail(e.target.value)} />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField label="Phone Number" fullWidth value={newPhone} onChange={(e) => setNewPhone(e.target.value)} />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Quota Selection</InputLabel>
                    <Select value={quota} onChange={(e) => setQuota(e.target.value)} label="Quota Selection">
                      <MenuItem value="MERIT">State Merit</MenuItem>
                      <MenuItem value="MANAGEMENT">Management Quota</MenuItem>
                      <MenuItem value="SPORTS">Sports Category</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Category</InputLabel>
                    <Select value={category} onChange={(e) => setCategory(e.target.value)} label="Category">
                      <MenuItem value="GENERAL">General Merit</MenuItem>
                      <MenuItem value="OBC">OBC</MenuItem>
                      <MenuItem value="SC_ST">SC / ST</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <Button variant="contained" color="primary" onClick={handleCreateDraft}>
                    Create Application Draft
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* TAB 3: DOCUMENT VERIFICATION */}
      {tab === 'VERIFY' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Document Verification Panel</Typography>
          {applications.filter(a => a.documents.length > 0).map(app => (
            <Card key={app.id} sx={{ mb: 3, border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 1 }}>
                  {app.applicantName} ({app.applicationNumber})
                </Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Category</TableCell>
                      <TableCell>File Name</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">Verify Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {app.documents.map((doc: any) => (
                      <TableRow key={doc.id}>
                        <TableCell>{doc.category}</TableCell>
                        <TableCell sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <DocIcon fontSize="small" /> {doc.name}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={doc.status}
                            size="small"
                            color={doc.status === 'VERIFIED' ? 'success' : doc.status === 'REJECTED' ? 'error' : 'warning'}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton color="success" onClick={() => handleVerifyDoc(app.id, doc.id, true)}>
                            <ApproveIcon />
                          </IconButton>
                          <IconButton color="error" onClick={() => handleVerifyDoc(app.id, doc.id, false)}>
                            <RejectIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ))}
        </Paper>
      )}

      {/* TAB 4: ENROLLMENTS CONSOLE */}
      {tab === 'ENROLL' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Enrolled Academic Student Cards</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Enrollment No</TableCell>
                  <TableCell>Student Name</TableCell>
                  <TableCell>Institutional USN</TableCell>
                  <TableCell>Assigned Roll No</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {enrollments.map((enr) => (
                  <TableRow key={enr.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{enr.enrollmentNumber}</TableCell>
                    <TableCell>{enr.studentName}</TableCell>
                    <TableCell>{enr.usn}</TableCell>
                    <TableCell>{enr.rollNo}</TableCell>
                    <TableCell>
                      <Chip label={enr.status} size="small" color="success" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 5: ANALYTICS */}
      {tab === 'ANALYTICS' && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={4}>
            <Card sx={{ bgcolor: 'primary.light', color: 'primary.contrastText', borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6">Total Applications</Typography>
                <Typography variant="h3" fontWeight="bold">120</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card sx={{ bgcolor: 'success.light', color: 'success.contrastText', borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6">Enrolled Ratio</Typography>
                <Typography variant="h3" fontWeight="bold">78%</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card sx={{ bgcolor: 'warning.light', color: 'warning.contrastText', borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6">Conversion count</Typography>
                <Typography variant="h3" fontWeight="bold">94 candidates</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* DIALOG: REVIEW APPLICATION */}
      <Dialog open={reviewOpen} onClose={() => setReviewOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>Review Applicant Submission</DialogTitle>
        <DialogContent>
          <TextField
            label="Internal Notes"
            multiline
            rows={3}
            fullWidth
            sx={{ mt: 2 }}
            value={reviewComment}
            onChange={(e) => setReviewComment(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewOpen(false)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={() => handleReviewAction('REJECTED')}>Reject</Button>
          <Button color="success" variant="contained" onClick={() => handleReviewAction('APPROVED')}>Approve</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdmissionDashboard;
