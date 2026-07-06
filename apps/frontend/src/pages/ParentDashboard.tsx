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
  Chip,
  Tab,
  Tabs,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Divider,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import {
  Person as PersonIcon,
  Notifications as NotifIcon,
  Message as MsgIcon,
  CheckCircle as PresentIcon,
  AttachMoney as FeeIcon,
  Assignment as TaskIcon
} from '@mui/icons-material';

export const ParentDashboard: React.FC = () => {
  const [tab, setTab] = useState<'OVERVIEW' | 'ATTENDANCE' | 'RESULTS' | 'ASSIGNMENTS' | 'FEES' | 'MESSAGES' | 'NOTIFICATIONS'>('OVERVIEW');

  // Multi-student linkage selection
  const [linkedStudents] = useState<any[]>([
    { id: 'stud-1', name: 'Samantha Vance', usn: 'USN202609A', rollNo: 'ROLL-101', class: 'B.Tech CSE Semester 3' },
    { id: 'stud-2', name: 'Marcus Vance', usn: 'USN202611B', rollNo: 'ROLL-102', class: 'B.Tech CSE Semester 1' }
  ]);
  const [selectedStudent, setSelectedStudent] = useState<string>('stud-1');

  // Notifications state
  const [notifications, setNotifications] = useState<any[]>([
    { id: 'n-1', title: 'Low Attendance Alert', message: 'Samantha\'s attendance in Computer Networks is below 75%.', category: 'ATTENDANCE_ALERT', isRead: false, date: '2026-07-06' },
    { id: 'n-2', title: 'Fee Payment Received', message: 'Invoice INV-2026-001 has been marked as partially paid.', category: 'FEE_REMINDER', isRead: true, date: '2026-07-05' }
  ]);

  // Messages state
  const [messages, setMessages] = useState<any[]>([
    { id: 'm-1', sender: 'Prof. Cooper (Mentor)', content: 'Samantha has been performing excellently in programming assignments.', date: '2026-07-06' }
  ]);
  const [newMsg, setNewMsg] = useState('');

  const currentStudent = linkedStudents.find(s => s.id === selectedStudent);

  const handleSendMessage = () => {
    if (!newMsg) return;
    setMessages([...messages, { id: `m-${Date.now()}`, sender: 'Parent (You)', content: newMsg, date: 'Just now' }]);
    setNewMsg('');
  };

  const handleMarkAsRead = (id: string) => {
    setNotifications(notifications.map(n => n.id === id ? { ...n, isRead: true } : n));
  };

  return (
    <Box sx={{ p: 4 }}>
      {/* Header with Linked Student Switcher */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2, mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary">Parent Portal</Typography>
          <Typography variant="subtitle1" color="textSecondary">Monitor student academic lifecycles, schedules, and billing statements.</Typography>
        </Box>
        <FormControl sx={{ minWidth: 220 }}>
          <InputLabel>Active Student Context</InputLabel>
          <Select
            value={selectedStudent}
            onChange={(e) => setSelectedStudent(e.target.value)}
            label="Active Student Context"
          >
            {linkedStudents.map(s => (
              <MenuItem key={s.id} value={s.id}>
                {s.name} ({s.rollNo})
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tab} onChange={(_, val) => setTab(val)} textColor="primary" indicatorColor="primary">
          <Tab value="OVERVIEW" label="Overview" />
          <Tab value="ATTENDANCE" label="Attendance" />
          <Tab value="RESULTS" label="Academic Results" />
          <Tab value="ASSIGNMENTS" label="Assignments" />
          <Tab value="FEES" label="Billing & Fees" />
          <Tab value="MESSAGES" label="Direct Messages" />
          <Tab value="NOTIFICATIONS" label="Notifications Inbox" />
        </Tabs>
      </Box>

      {/* TAB 1: OVERVIEW */}
      {tab === 'OVERVIEW' && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Alert severity="info" sx={{ borderRadius: 2 }}>
              Currently inspecting academic summaries for <strong>{currentStudent?.name}</strong> ({currentStudent?.class}).
            </Alert>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card sx={{ borderRadius: 3, border: '1px solid #e2e8f0' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <PresentIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h6">Attendance Ratio</Typography>
                <Typography variant="h4" fontWeight="bold" color="primary">84.5%</Typography>
                <Chip label="Stable" color="success" size="small" sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card sx={{ borderRadius: 3, border: '1px solid #e2e8f0' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <PersonIcon color="success" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h6">Cumulative CGPA</Typography>
                <Typography variant="h4" fontWeight="bold" color="success">8.60</Typography>
                <Chip label="Top 10%" color="success" size="small" sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card sx={{ borderRadius: 3, border: '1px solid #e2e8f0' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <TaskIcon color="warning" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h6">Pending Tasks</Typography>
                <Typography variant="h4" fontWeight="bold" color="warning">3</Typography>
                <Chip label="Due Soon" color="warning" size="small" sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card sx={{ borderRadius: 3, border: '1px solid #e2e8f0' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <FeeIcon color="error" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h6">Outstanding Fees</Typography>
                <Typography variant="h4" fontWeight="bold" color="error">40,000 INR</Typography>
                <Chip label="Overdue" color="error" size="small" sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* TAB 2: ATTENDANCE */}
      {tab === 'ATTENDANCE' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Monthly Attendance Ledger</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Course Module</TableCell>
                  <TableCell>Total Sessions</TableCell>
                  <TableCell>Attended Sessions</TableCell>
                  <TableCell>Attendance ratio</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Computer Networks (CS-301)</TableCell>
                  <TableCell>45</TableCell>
                  <TableCell>31</TableCell>
                  <TableCell sx={{ color: 'error.main', fontWeight: 'bold' }}>68.8%</TableCell>
                  <TableCell><Chip label="Low Attendance Alert" color="error" size="small" /></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Database Systems (CS-302)</TableCell>
                  <TableCell>40</TableCell>
                  <TableCell>37</TableCell>
                  <TableCell sx={{ color: 'success.main', fontWeight: 'bold' }}>92.5%</TableCell>
                  <TableCell><Chip label="Excellent" color="success" size="small" /></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 3: RESULTS */}
      {tab === 'RESULTS' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Grades & Results Compilation</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Subject Name</TableCell>
                  <TableCell>Internal Assessment</TableCell>
                  <TableCell>End-Sem Exam Marks</TableCell>
                  <TableCell>Grade Point Awarded</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Operating Systems</TableCell>
                  <TableCell>44 / 50</TableCell>
                  <TableCell>85 / 100</TableCell>
                  <TableCell>A+ (9.0)</TableCell>
                  <TableCell><Chip label="PASS" color="success" size="small" /></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Software Architecture</TableCell>
                  <TableCell>38 / 50</TableCell>
                  <TableCell>78 / 100</TableCell>
                  <TableCell>A (8.0)</TableCell>
                  <TableCell><Chip label="PASS" color="success" size="small" /></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 4: ASSIGNMENTS */}
      {tab === 'ASSIGNMENTS' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Assignments Checklist</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Assignment Title</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell>Submission Status</TableCell>
                  <TableCell>Obtained Marks</TableCell>
                  <TableCell>Faculty Remarks</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>TCP/IP Simulation Lab</TableCell>
                  <TableCell>2026-07-10</TableCell>
                  <TableCell><Chip label="PENDING" color="warning" size="small" /></TableCell>
                  <TableCell>--</TableCell>
                  <TableCell>No submission files uploaded yet.</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Entity Relationship Design Project</TableCell>
                  <TableCell>2026-06-30</TableCell>
                  <TableCell><Chip label="SUBMITTED" color="success" size="small" /></TableCell>
                  <TableCell>45 / 50</TableCell>
                  <TableCell>Well drafted schema relations.</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 5: BILLING & FEES */}
      {tab === 'FEES' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Fee Statements</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Invoice Number</TableCell>
                  <TableCell>Deductions Applied</TableCell>
                  <TableCell>Total Invoiced</TableCell>
                  <TableCell>Paid Amount</TableCell>
                  <TableCell>Remaining Balance</TableCell>
                  <TableCell>Due Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>INV-2026-001</TableCell>
                  <TableCell>15,000 INR (Merit Scholarship)</TableCell>
                  <TableCell>60,000 INR</TableCell>
                  <TableCell>20,000 INR</TableCell>
                  <TableCell sx={{ color: 'error.main', fontWeight: 'bold' }}>40,000 INR</TableCell>
                  <TableCell>2026-12-31</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 6: MESSAGES */}
      {tab === 'MESSAGES' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Secure Direct Messages (Faculty & Mentor)</Typography>
          <Divider />
          <List sx={{ maxHeight: 300, overflowY: 'auto', mb: 3 }}>
            {messages.map(m => (
              <ListItem key={m.id}>
                <ListItemText
                  primary={<strong>{m.sender}</strong>}
                  secondary={
                    <>
                      <Typography component="span" variant="body2" color="textPrimary">
                        {m.content}
                      </Typography>
                      {` — ${m.date}`}
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Type message..."
              fullWidth
              value={newMsg}
              onChange={(e) => setNewMsg(e.target.value)}
            />
            <Button variant="contained" endIcon={<MsgIcon />} onClick={handleSendMessage}>
              Send
            </Button>
          </Box>
        </Paper>
      )}

      {/* TAB 7: NOTIFICATIONS */}
      {tab === 'NOTIFICATIONS' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Alerts & Notice Inboxes</Typography>
          <List>
            {notifications.map(n => (
              <ListItem
                key={n.id}
                sx={{
                  bgcolor: n.isRead ? 'transparent' : 'action.hover',
                  borderRadius: 2,
                  mb: 1
                }}
                secondaryAction={
                  !n.isRead && (
                    <Button size="small" onClick={() => handleMarkAsRead(n.id)}>
                      Mark Read
                    </Button>
                  )
                }
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <NotifIcon color={n.isRead ? 'disabled' : 'primary'} />
                      <strong>{n.title}</strong>
                      <Chip label={n.category} size="small" />
                    </Box>
                  }
                  secondary={`${n.message} | Received: ${n.date}`}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
};

export default ParentDashboard;
