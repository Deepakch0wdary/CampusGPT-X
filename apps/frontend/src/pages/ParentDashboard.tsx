import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Tab,
  Tabs,
  Card,
  CardContent,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Alert,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  ChildCare as ChildIcon,
  HomeWork as HostelIcon,
  DirectionsBus as TransportIcon,
  Book as LibraryIcon
} from '@mui/icons-material';

export const ParentDashboard: React.FC = () => {
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<string>('OVERVIEW');
  const [loading, setLoading] = useState<boolean>(true);
  const [_error, setError] = useState<string | null>(null);

  // Parent Portal Data States for Selected Child
  const [overview, setOverview] = useState<any>(null);
  const [academics, setAcademics] = useState<any>(null);
  const [attendance, setAttendance] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [exams, setExams] = useState<any[]>([]);
  const [results, setResults] = useState<any[]>([]);
  const [fees, setFees] = useState<any[]>([]);
  const [library, setLibrary] = useState<any>(null);
  const [hostel, setHostel] = useState<any>(null);
  const [transport, setTransport] = useState<any>(null);
  const [meetings, setMeetings] = useState<any[]>([]);
  const [consents, setConsents] = useState<any[]>([]);
  const [preferences, setPreferences] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);

  // Dialog & Form States
  const [openMeetingDlg, setOpenMeetingDlg] = useState(false);
  const [meetingForm, setMeetingForm] = useState({
    teacherUserId: '',
    scheduledAt: '',
    agenda: '',
    meetingMode: 'ONLINE'
  });

  const getHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  };

  // Fetch children list on load
  useEffect(() => {
    fetchChildren();
  }, []);

  // Fetch child-specific details when child switcher changes
  useEffect(() => {
    if (selectedChildId) {
      fetchChildData(selectedChildId);
    }
  }, [selectedChildId]);

  const fetchChildren = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/v1/parent/children', { headers: getHeaders() });
      if (!res.ok) throw new Error('Failed to fetch linked children');
      const data = await res.json();
      setChildren(data);
      if (data.length > 0) {
        setSelectedChildId(data[0].id);
      } else {
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const fetchChildData = async (studentId: string) => {
    try {
      setLoading(true);
      setError(null);

      // Concurrently load statistics
      const [
        overviewRes,
        academicsRes,
        attendanceRes,
        assignmentsRes,
        examsRes,
        resultsRes,
        feesRes,
        libraryRes,
        hostelRes,
        transportRes,
        meetingsRes,
        consentsRes,
        prefsRes,
        alertsRes
      ] = await Promise.all([
        fetch(`/api/v1/parent/children/${studentId}/overview`, { headers: getHeaders() }),
        fetch(`/api/v1/parent/children/${studentId}/academics`, { headers: getHeaders() }),
        fetch(`/api/v1/parent/children/${studentId}/attendance`, { headers: getHeaders() }),
        fetch(`/api/v1/parent/children/${studentId}/assignments`, { headers: getHeaders() }),
        fetch(`/api/v1/parent/children/${studentId}/exams`, { headers: getHeaders() }),
        fetch(`/api/v1/parent/children/${studentId}/results`, { headers: getHeaders() }),
        fetch(`/api/v1/parent/children/${studentId}/fees`, { headers: getHeaders() }),
        fetch(`/api/v1/parent/children/${studentId}/library`, { headers: getHeaders() }),
        fetch(`/api/v1/parent/children/${studentId}/hostel`, { headers: getHeaders() }),
        fetch(`/api/v1/parent/children/${studentId}/transport`, { headers: getHeaders() }),
        fetch('/api/v1/parent/meetings', { headers: getHeaders() }),
        fetch('/api/v1/parent/consents', { headers: getHeaders() }),
        fetch('/api/v1/parent/notification-preferences', { headers: getHeaders() }),
        fetch(`/api/v1/parent/alerts?studentId=${studentId}`, { headers: getHeaders() })
      ]);

      if (overviewRes.ok) setOverview(await overviewRes.json());
      if (academicsRes.ok) setAcademics(await academicsRes.json());
      if (attendanceRes.ok) setAttendance(await attendanceRes.json());
      if (assignmentsRes.ok) setAssignments(await assignmentsRes.json());
      if (examsRes.ok) setExams(await examsRes.json());
      if (resultsRes.ok) setResults(await resultsRes.json());
      if (feesRes.ok) setFees(await feesRes.json());
      if (libraryRes.ok) setLibrary(await libraryRes.json());
      if (hostelRes.ok) setHostel(await hostelRes.json());
      if (transportRes.ok) setTransport(await transportRes.json());
      if (meetingsRes.ok) setMeetings(await meetingsRes.json());
      if (consentsRes.ok) setConsents(await consentsRes.json());
      if (prefsRes.ok) setPreferences(await prefsRes.json());
      if (alertsRes.ok) setAlerts(await alertsRes.json());

      setLoading(false);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleConsentResponse = async (consentId: string, status: string) => {
    try {
      const res = await fetch(`/api/v1/parent/consents/${consentId}/respond`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        // Refresh consents
        const updated = await fetch('/api/v1/parent/consents', { headers: getHeaders() });
        if (updated.ok) setConsents(await updated.json());
      }
    } catch (err: any) {
      alert("Failed to submit consent response.");
    }
  };

  const handlePreferenceToggle = async (field: string, currentVal: boolean) => {
    try {
      const res = await fetch('/api/v1/parent/notification-preferences', {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ [field]: !currentVal })
      });
      if (res.ok) {
        setPreferences(await res.json());
      }
    } catch (err: any) {
      alert("Failed to update notification preferences.");
    }
  };

  const handleCreateMeeting = async () => {
    try {
      const res = await fetch('/api/v1/parent/meetings', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          studentId: selectedChildId,
          teacherUserId: meetingForm.teacherUserId,
          scheduledAt: new Date(meetingForm.scheduledAt).toISOString(),
          agenda: meetingForm.agenda,
          meetingMode: meetingForm.meetingMode
        })
      });
      if (res.ok) {
        setOpenMeetingDlg(false);
        const updated = await fetch('/api/v1/parent/meetings', { headers: getHeaders() });
        if (updated.ok) setMeetings(await updated.json());
        setMeetingForm({ teacherUserId: '', scheduledAt: '', agenda: '', meetingMode: 'ONLINE' });
      } else {
        const data = await res.json();
        alert(data.detail || "Failed to schedule meeting.");
      }
    } catch (err: any) {
      alert("Error scheduling meeting request.");
    }
  };

  if (loading && children.length === 0) {
    return (
      <Box p={3}>
        <Typography variant="h5">Loading Linked Family Profile...</Typography>
      </Box>
    );
  }

  if (children.length === 0) {
    return (
      <Box p={3}>
        <Alert severity="warning">No linked student records found for this parent account. Please contact administrative staff for child verification.</Alert>
      </Box>
    );
  }

  const selectedChild = children.find(c => c.id === selectedChildId);

  return (
    <Box p={3} sx={{ flexGrow: 1, backgroundColor: '#f9f9f9', minHeight: '100vh' }}>

      {/* Context Switcher & Child profile Header */}
      <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }} elevation={1}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={6}>
            <Box display="flex" alignItems="center" gap={1}>
              <ChildIcon color="primary" fontSize="large" />
              <Typography variant="h4" fontWeight="600">Parent Portal</Typography>
            </Box>
            <Typography variant="body2" color="textSecondary" mt={0.5}>
              Secure multi-child context switching dashboard. Enforcing object-level child safety checks.
            </Typography>
          </Grid>
          <Grid item xs={12} md={6} display="flex" justifyContent={{ md: 'flex-end', xs: 'flex-start' }}>
            <FormControl sx={{ minWidth: 250 }}>
              <InputLabel>Switch Child Context</InputLabel>
              <Select
                value={selectedChildId}
                label="Switch Child Context"
                onChange={(e) => setSelectedChildId(e.target.value as string)}
              >
                {children.map(child => (
                  <MenuItem key={child.id} value={child.id}>
                    {child.name} ({child.relationship})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {academics && (
          <Box mt={2}>
            <Divider sx={{ my: 1.5 }} />
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="textSecondary">Department</Typography>
                <Typography variant="body1" fontWeight="600">{academics.department}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="textSecondary">Section</Typography>
                <Typography variant="body1" fontWeight="600">{academics.section}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="textSecondary">Link Status</Typography>
                <Box mt={0.5}>
                  <Chip size="small" label={selectedChild?.status || 'VERIFIED'} color="success" />
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="textSecondary">Primary Contact</Typography>
                <Typography variant="body1" fontWeight="600">{selectedChild?.isPrimaryContact ? 'Yes' : 'No'}</Typography>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>

      {/* Low Attendance / Overdue Alerts */}
      {alerts.length > 0 && (
        <Box mb={3}>
          {alerts.map((al, idx) => (
            <Alert key={idx} severity={al.severity === 'HIGH' ? 'error' : 'warning'} sx={{ mb: 1 }}>
              <strong>{al.title}:</strong> {al.message}
            </Alert>
          ))}
        </Box>
      )}

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onChange={(_e, v) => setActiveTab(v)}
        indicatorColor="primary"
        textColor="primary"
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="Dashboard Metrics" value="OVERVIEW" />
        <Tab label="Attendance" value="ATTENDANCE" />
        <Tab label="Assignments" value="ASSIGNMENTS" />
        <Tab label="Exams & Timetable" value="EXAMS" />
        <Tab label="Grades & Results" value="RESULTS" />
        <Tab label="Invoices & Finance" value="FEES" />
        <Tab label="Services (Hostel/Transport)" value="SERVICES" />
        <Tab label="Teacher Meetings" value="MEETINGS" />
        <Tab label="Release Consents" value="CONSENTS" />
        <Tab label="Alert Channels" value="SETTINGS" />
      </Tabs>

      {/* Tab Panels */}

      {/* OVERVIEW PANEL */}
      {activeTab === 'OVERVIEW' && overview && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">Attendance Percentage</Typography>
                <Typography variant="h3" mt={1} fontWeight="bold" color="primary.main">
                  {overview.attendancePercentage.toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {overview.presentDays} Present, {overview.absentDays} Absent
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">SGPA Performance</Typography>
                <Typography variant="h3" mt={1} fontWeight="bold" color="success.main">
                  {overview.latestSGPA > 0 ? overview.latestSGPA : 'N/A'}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Published semester grades [RULE-BASED INSIGHT]
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">Pending Tasks</Typography>
                <Typography variant="h3" mt={1} fontWeight="bold" color="warning.main">
                  {overview.pendingAssignments}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Assignments requiring student submission
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">Outstanding Fees</Typography>
                <Typography variant="h3" mt={1} fontWeight="bold" color="error.main">
                  ₹{overview.outstandingFees}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Unpaid tuition / library dues
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Quick Info details */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 2 }}>
              <Typography variant="h6" fontWeight="600" mb={2}>Hostel Room Assignment</Typography>
              {overview.hostelRoom ? (
                <Alert severity="info" icon={<HostelIcon />}>
                  Currently residing in: <strong>{overview.hostelRoom}</strong>
                </Alert>
              ) : (
                <Typography variant="body1" color="textSecondary">No active hostel boarding allocation found. [Honest Empty State]</Typography>
              )}
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 2 }}>
              <Typography variant="h6" fontWeight="600" mb={2}>Transport Commute Details</Typography>
              {overview.transportRoute ? (
                <Alert severity="info" icon={<TransportIcon />}>
                  Subscribed Shuttle Route: <strong>{overview.transportRoute}</strong>
                </Alert>
              ) : (
                <Typography variant="body1" color="textSecondary">No active school transport subscription registered. [Honest Empty State]</Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* ATTENDANCE PANEL */}
      {activeTab === 'ATTENDANCE' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight="600">Child Attendance Audit Trail</Typography>
            <Chip label="Read-Only View" color="warning" size="small" />
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Session Date</strong></TableCell>
                  <TableCell><strong>Subject Course</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Remarks</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {attendance.length > 0 ? (
                  attendance.map(row => (
                    <TableRow key={row.id}>
                      <TableCell>{row.sessionDate}</TableCell>
                      <TableCell>{row.subject}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={row.status}
                          color={row.status === 'PRESENT' ? 'success' : row.status === 'ABSENT' ? 'error' : 'warning'}
                        />
                      </TableCell>
                      <TableCell>{row.remarks || 'N/A'}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={4} align="center">No attendance records recorded.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* ASSIGNMENTS PANEL */}
      {activeTab === 'ASSIGNMENTS' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight="600">Course Assignments</Typography>
            <Chip label="Read-Only View" color="warning" size="small" />
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Assignment Title</strong></TableCell>
                  <TableCell><strong>Due Date</strong></TableCell>
                  <TableCell><strong>Submission Status</strong></TableCell>
                  <TableCell><strong>Grade</strong></TableCell>
                  <TableCell><strong>Marks</strong></TableCell>
                  <TableCell><strong>Feedback Notes</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {assignments.length > 0 ? (
                  assignments.map(row => (
                    <TableRow key={row.id}>
                      <TableCell>{row.title}</TableCell>
                      <TableCell>{new Date(row.dueDate).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={row.submitted ? 'Submitted' : 'Pending'}
                          color={row.submitted ? 'success' : 'error'}
                        />
                      </TableCell>
                      <TableCell>{row.grade || 'N/A'}</TableCell>
                      <TableCell>{row.marks !== null ? row.marks : 'N/A'}</TableCell>
                      <TableCell>{row.feedback || 'N/A'}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} align="center">No assignments assigned to child's section.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* EXAMS PANEL */}
      {activeTab === 'EXAMS' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight="600" mb={2}>Examination Schedules Timetables</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Exam Name</strong></TableCell>
                  <TableCell><strong>Subject</strong></TableCell>
                  <TableCell><strong>Exam Date</strong></TableCell>
                  <TableCell><strong>Timings</strong></TableCell>
                  <TableCell><strong>Room Number</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {exams.length > 0 ? (
                  exams.map(row => (
                    <TableRow key={row.id}>
                      <TableCell>{row.examName}</TableCell>
                      <TableCell>{row.subject}</TableCell>
                      <TableCell>{new Date(row.date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        {new Date(row.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(row.endTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </TableCell>
                      <TableCell>{row.room}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} align="center">No upcoming examinations scheduled.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* RESULTS PANEL */}
      {activeTab === 'RESULTS' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight="600" mb={2}>Child Term Scores & Grades</Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            Only finalized, published results are visible. Draft grades are filtered out at the API layer.
          </Alert>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Exam Name</strong></TableCell>
                  <TableCell><strong>Subject Course</strong></TableCell>
                  <TableCell><strong>Marks Obtained</strong></TableCell>
                  <TableCell><strong>Grade Awarded</strong></TableCell>
                  <TableCell><strong>Credits</strong></TableCell>
                  <TableCell><strong>Published Date</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {results.length > 0 ? (
                  results.map(row => (
                    <TableRow key={row.id}>
                      <TableCell>{row.examName}</TableCell>
                      <TableCell>{row.subjectName}</TableCell>
                      <TableCell>{row.marksObtained}</TableCell>
                      <TableCell>
                        <Chip label={row.grade} size="small" color="primary" variant="outlined" />
                      </TableCell>
                      <TableCell>{row.credits}</TableCell>
                      <TableCell>{new Date(row.publishedAt).toLocaleDateString()}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} align="center">No published exam results found.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* INVOICES PANEL */}
      {activeTab === 'FEES' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight="600">Finance & Fee Invoices</Typography>
            <Chip label="Read-Only View" color="warning" size="small" />
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Invoice Reference</strong></TableCell>
                  <TableCell><strong>Fee Category/Title</strong></TableCell>
                  <TableCell><strong>Total Amount</strong></TableCell>
                  <TableCell><strong>Amount Paid</strong></TableCell>
                  <TableCell><strong>Outstanding Balance</strong></TableCell>
                  <TableCell><strong>Due Date</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {fees.length > 0 ? (
                  fees.map(row => (
                    <TableRow key={row.id}>
                      <TableCell>{row.invoiceNumber}</TableCell>
                      <TableCell>{row.title}</TableCell>
                      <TableCell>₹{row.amount}</TableCell>
                      <TableCell>₹{row.paidAmount}</TableCell>
                      <TableCell><strong>₹{row.outstanding}</strong></TableCell>
                      <TableCell>{new Date(row.dueDate).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={row.status}
                          color={row.status === 'PAID' ? 'success' : row.status === 'PARTIALLY_PAID' ? 'warning' : 'error'}
                        />
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} align="center">No financial fee invoices found.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* SERVICES PANEL */}
      {activeTab === 'SERVICES' && (
        <Grid container spacing={3}>

          {/* Hostel card info */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 2 }}>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <HostelIcon color="primary" />
                <Typography variant="h6" fontWeight="600">Smart Hostel Management</Typography>
              </Box>
              {hostel && hostel.allocated ? (
                <Box>
                  <Typography variant="body1" mb={1}>
                    Residence Block: <strong>{hostel.roomDetails.hostelName} - {hostel.roomDetails.blockName}</strong>
                  </Typography>
                  <Typography variant="body1" mb={2}>
                    Assigned Room Number: <strong>{hostel.roomDetails.roomNumber}</strong> (Floor {hostel.roomDetails.floor})
                  </Typography>

                  <Typography variant="subtitle2" fontWeight="600" mb={1}>Leave Requests History</Typography>
                  {hostel.leaves && hostel.leaves.length > 0 ? (
                    hostel.leaves.map((l: any) => (
                      <Box key={l.id} sx={{ p: 1, mb: 1, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                        <Typography variant="body2">Dates: {new Date(l.startDate).toLocaleDateString()} to {new Date(l.endDate).toLocaleDateString()}</Typography>
                        <Typography variant="body2">Reason: {l.reason}</Typography>
                        <Box mt={0.5}>
                          <Chip size="small" label={l.status} color={l.status === 'APPROVED' ? 'success' : 'warning'} />
                        </Box>
                      </Box>
                    ))
                  ) : (
                    <Typography variant="body2" color="textSecondary">No leave requests logged.</Typography>
                  )}
                </Box>
              ) : (
                <Typography variant="body1" color="textSecondary">No hostel room currently assigned.</Typography>
              )}
            </Paper>
          </Grid>

          {/* Transport Card info */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 2 }}>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <TransportIcon color="primary" />
                <Typography variant="h6" fontWeight="600">Smart Transport tracking</Typography>
              </Box>
              {transport && transport.assigned ? (
                <Box>
                  <Typography variant="body1" mb={1}>
                    Route Code: <strong>{transport.routeCode}</strong> ({transport.routeName})
                  </Typography>
                  <Typography variant="body1" mb={1}>
                    Pickup Location stop: <strong>{transport.pickupStop}</strong>
                  </Typography>
                  <Typography variant="body1" mb={1}>
                    Dropoff Location stop: <strong>{transport.dropStop}</strong>
                  </Typography>
                  <Typography variant="body1" mb={2}>
                    Assigned vehicle Code: <strong>{transport.vehicleCode}</strong> (Driver: {transport.driverName})
                  </Typography>

                  {/* Simulated Telemetry GPS map card */}
                  <Paper sx={{ p: 2, backgroundColor: '#eef5fc', border: '1px dashed #1976d2' }}>
                    <Typography variant="subtitle2" color="primary" fontWeight="bold">GPS SIMULATOR DATA</Typography>
                    <Typography variant="body2" color="textSecondary" mt={0.5}>
                      Latitude: {transport.gps.latitude} | Longitude: {transport.gps.longitude}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Estimated Speed: {transport.gps.speedKph} Km/h | Heading: {transport.gps.heading}°
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'orange', display: 'block', mt: 1, fontWeight: 'bold' }}>
                      [SIMULATED DEMO DATA fallbacks mapped to Bangalore limits]
                    </Typography>
                  </Paper>
                </Box>
              ) : (
                <Typography variant="body1" color="textSecondary">No active transport loop registered.</Typography>
              )}
            </Paper>
          </Grid>

          {/* Library Card Info */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3, borderRadius: 2 }}>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <LibraryIcon color="primary" />
                <Typography variant="h6" fontWeight="600">Library Loans & Checkouts</Typography>
              </Box>
              {library && library.activeLoans && library.activeLoans.length > 0 ? (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Book Title</strong></TableCell>
                        <TableCell><strong>Checkout Date</strong></TableCell>
                        <TableCell><strong>Due Date</strong></TableCell>
                        <TableCell><strong>Status</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {library.activeLoans.map((l: any) => (
                        <TableRow key={l.id}>
                          <TableCell>{l.bookTitle}</TableCell>
                          <TableCell>{new Date(l.issuedAt).toLocaleDateString()}</TableCell>
                          <TableCell>{new Date(l.dueDate).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <Chip size="small" label={l.status} color={l.status === 'ACTIVE' ? 'success' : 'error'} />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body1" color="textSecondary">No books currently checked out by child.</Typography>
              )}
            </Paper>
          </Grid>

        </Grid>
      )}

      {/* MEETINGS PANEL */}
      {activeTab === 'MEETINGS' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight="600">Parent Teacher Meetings Scheduled</Typography>
            <Button variant="contained" size="small" onClick={() => setOpenMeetingDlg(true)}>
              Request Teacher Meeting
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Child Name</strong></TableCell>
                  <TableCell><strong>Teacher Name</strong></TableCell>
                  <TableCell><strong>Meeting Date</strong></TableCell>
                  <TableCell><strong>Duration</strong></TableCell>
                  <TableCell><strong>Mode</strong></TableCell>
                  <TableCell><strong>Agenda Summary</strong></TableCell>
                  <TableCell><strong>Link/Location</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {meetings.length > 0 ? (
                  meetings.map(row => (
                    <TableRow key={row.id}>
                      <TableCell>{row.studentName}</TableCell>
                      <TableCell>{row.teacherName}</TableCell>
                      <TableCell>{new Date(row.scheduledAt).toLocaleString()}</TableCell>
                      <TableCell>{row.durationMinutes} mins</TableCell>
                      <TableCell>{row.meetingMode}</TableCell>
                      <TableCell>{row.agenda}</TableCell>
                      <TableCell>{row.locationOrLink || 'To be shared'}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={row.status}
                          color={row.status === 'APPROVED' ? 'success' : row.status === 'REQUESTED' ? 'warning' : 'error'}
                        />
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} align="center">No PTM meetings requested or scheduled.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* CONSENTS PANEL */}
      {activeTab === 'CONSENTS' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight="600" mb={2}>Mandatory Activity Release Forms & Consents</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Child</strong></TableCell>
                  <TableCell><strong>Consent Type</strong></TableCell>
                  <TableCell><strong>Consent Title</strong></TableCell>
                  <TableCell><strong>Description Details</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell align="right"><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {consents.length > 0 ? (
                  consents.map(row => (
                    <TableRow key={row.id}>
                      <TableCell>{row.studentName}</TableCell>
                      <TableCell>
                        <Chip size="small" label={row.consentType} variant="outlined" />
                      </TableCell>
                      <TableCell>{row.title}</TableCell>
                      <TableCell>{row.description}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={row.status}
                          color={row.status === 'APPROVED' ? 'success' : row.status === 'DECLINED' ? 'error' : 'warning'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {row.status === 'PENDING' && (
                          <Box display="flex" gap={1} justifyContent="flex-end">
                            <Button size="small" color="success" variant="outlined" onClick={() => handleConsentResponse(row.id, 'APPROVED')}>
                              Approve
                            </Button>
                            <Button size="small" color="error" variant="outlined" onClick={() => handleConsentResponse(row.id, 'DECLINED')}>
                              Decline
                            </Button>
                          </Box>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} align="center">No consent requests waiting response.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* SETTINGS PANEL */}
      {activeTab === 'SETTINGS' && preferences && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight="600" mb={2}>Configure Automated SMS / Email Notification Alerts</Typography>
          <Alert severity="info" sx={{ mb: 3 }}>
            Alerts triggered by changes are saved locally. External gateways run via mock channel adapters. [ADAPTER NOT CONFIGURED]
          </Alert>
          <Grid container spacing={2}>
            {[
              { label: 'Attendance warnings & absence alerts', key: 'attendanceAlerts' },
              { label: 'Assignment submission updates', key: 'assignmentAlerts' },
              { label: 'Exam timetable reminders', key: 'examAlerts' },
              { label: 'Result card published warnings', key: 'resultAlerts' },
              { label: 'Outstanding balance fee dues alerts', key: 'feeAlerts' },
              { label: 'Library loan overdue reminders', key: 'libraryAlerts' },
              { label: 'Hostel emergency updates', key: 'hostelAlerts' },
              { label: 'Transport loop delay warnings', key: 'transportAlerts' },
              { label: 'Critical security alerts', key: 'emergencyAlerts' },
              { label: 'Event schedules reminders', key: 'eventAlerts' }
            ].map(pref => (
              <Grid item xs={12} sm={6} key={pref.key}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences[pref.key] || false}
                      onChange={() => handlePreferenceToggle(pref.key, preferences[pref.key])}
                      color="primary"
                    />
                  }
                  label={pref.label}
                />
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Meeting Booking dialog */}
      <Dialog open={openMeetingDlg} onClose={() => setOpenMeetingDlg(false)}>
        <DialogTitle>Request Parent-Teacher Meeting</DialogTitle>
        <DialogContent sx={{ p: 3 }}>
          <Box display="flex" flexDirection="column" gap={2} mt={1} minWidth={350}>
            <TextField
              label="Teacher ID / Username"
              value={meetingForm.teacherUserId}
              onChange={(e) => setMeetingForm({ ...meetingForm, teacherUserId: e.target.value })}
              fullWidth
            />
            <TextField
              label="Meeting Date & Time"
              type="datetime-local"
              InputLabelProps={{ shrink: true }}
              value={meetingForm.scheduledAt}
              onChange={(e) => setMeetingForm({ ...meetingForm, scheduledAt: e.target.value })}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Meeting Mode</InputLabel>
              <Select
                value={meetingForm.meetingMode}
                label="Meeting Mode"
                onChange={(e) => setMeetingForm({ ...meetingForm, meetingMode: e.target.value as string })}
              >
                <MenuItem value="ONLINE">Online Video Call</MenuItem>
                <MenuItem value="IN_PERSON">In Person Meeting</MenuItem>
                <MenuItem value="PHONE">Phone Call</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Agenda & Purpose"
              multiline
              rows={3}
              value={meetingForm.agenda}
              onChange={(e) => setMeetingForm({ ...meetingForm, agenda: e.target.value })}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenMeetingDlg(false)}>Cancel</Button>
          <Button onClick={handleCreateMeeting} variant="contained" color="primary">
            Request Meeting
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
};
