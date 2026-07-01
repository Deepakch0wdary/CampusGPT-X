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
  Chip
} from '@mui/material';
import { 
  CalendarToday as CalendarIcon, 
  AccessTime as TimeIcon, 
  GridOn as GridIcon, 
  SwapHoriz as SwapIcon, 
  CheckCircle as CheckIcon, 
  ReportProblem as WarningIcon
} from '@mui/icons-material';

export const TimetableDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [userRole, setUserRole] = useState<string>('STUDENT');
  
  // Master Lists
  const [academicYears, setAcademicYears] = useState<any[]>([]);
  const [semesters, setSemesters] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [labs, setLabs] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  
  // Calendar & Events
  const [calendar, setCalendar] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [openEventDialog, setOpenEventDialog] = useState(false);
  const [eventForm, setEventForm] = useState({ title: '', eventDate: '', type: 'HOLIDAY', description: '' });

  // Period Slots
  const [slots, setSlots] = useState<any[]>([]);
  const [openSlotDialog, setOpenSlotDialog] = useState(false);
  const [slotForm, setSlotForm] = useState({ name: '', startTime: '', endTime: '', type: 'CLASS' });
  const [slotError, setSlotError] = useState<string | null>(null);

  // Timetables Headers & Entries
  const [grids, setGrids] = useState<any[]>([]);
  const [openGridDialog, setOpenGridDialog] = useState(false);
  const [gridForm, setGridForm] = useState({ name: '', academicYearId: '', semesterId: '', sectionId: '' });
  
  const [activeGridId, setActiveGridId] = useState<string>('');
  const [activeGrid, setActiveGrid] = useState<any>(null);
  const [openCellDialog, setOpenCellDialog] = useState(false);
  const [cellForm, setCellForm] = useState({ dayOfWeek: 'MONDAY', timeSlotId: '', subjectId: '', facultyId: '', roomId: '', labId: '' });
  const [clashResults, setClashResults] = useState<string[]>([]);
  
  // Substitute Faculty
  const [substitutes, setSubstitutes] = useState<any[]>([]);
  const [subForm, setSubForm] = useState({ date: '', timetableEntryId: '', substituteFacultyId: '' });
  const [selectedGridEntries, setSelectedGridEntries] = useState<any[]>([]);

  // Approvals
  const [openApproveDialog, setOpenApproveDialog] = useState(false);
  const [approveForm, setApproveForm] = useState({ timetableId: '', stage: 'MASTER_ADMIN', status: 'APPROVED', remarks: '' });

  // Schedules (Student / Faculty)
  const [roleSchedule, setRoleSchedule] = useState<any[]>([]);

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

      // Rooms
      const resRoom = await fetch('/api/v1/rooms', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resRoom.ok) {
        const payload = await resRoom.json();
        setRooms(payload.data || []);
      }
      
      // Laboratories
      const resLab = await fetch('/api/v1/laboratories', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resLab.ok) {
        const payload = await resLab.json();
        setLabs(payload.data || []);
      }

      // Teachers/Users
      const resUser = await fetch('/api/v1/users?limit=100', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resUser.ok) {
        const payload = await resUser.json();
        const usersList = payload.data.users || [];
        setTeachers(usersList.filter((u: any) => u.role === 'TEACHER'));
      }
      
      // Subjects
      const resSubj = await fetch('/api/v1/subjects', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSubj.ok) {
        const payload = await resSubj.json();
        setSubjects(payload.data || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchCalendar = async () => {
    try {
      const res = await fetch('/api/v1/timetable/calendar');
      if (res.ok) {
        const payload = await res.json();
        setCalendar(payload.data);
      }
      
      const resEvt = await fetch('/api/v1/timetable/calendar/events');
      if (resEvt.ok) {
        const payload = await resEvt.json();
        setEvents(payload.data.events || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createEvent = async () => {
    const token = localStorage.getItem('access_token');
    if (!calendar) return;
    try {
      const res = await fetch('/api/v1/timetable/calendar/events', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ...eventForm, calendarId: calendar.id })
      });
      if (res.ok) {
        setOpenEventDialog(false);
        setEventForm({ title: '', eventDate: '', type: 'HOLIDAY', description: '' });
        fetchCalendar();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSlots = async () => {
    try {
      const res = await fetch('/api/v1/timetable/slots');
      if (res.ok) {
        const payload = await res.json();
        setSlots(payload.data.slots || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createSlot = async () => {
    const token = localStorage.getItem('access_token');
    setSlotError(null);
    try {
      const res = await fetch('/api/v1/timetable/slots', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(slotForm)
      });
      if (res.ok) {
        setOpenSlotDialog(false);
        setSlotForm({ name: '', startTime: '', endTime: '', type: 'CLASS' });
        fetchSlots();
      } else {
        const payload = await res.json();
        setSlotError(payload.message || "Failed to create slot due to overlap validation.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchGrids = async () => {
    try {
      const res = await fetch('/api/v1/timetable/grids');
      if (res.ok) {
        const payload = await res.json();
        setGrids(payload.data.grids || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createGrid = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/timetable/grids', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(gridForm)
      });
      if (res.ok) {
        setOpenGridDialog(false);
        setGridForm({ name: '', academicYearId: '', semesterId: '', sectionId: '' });
        fetchGrids();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadGridDetail = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/timetable/grids/${id}`);
      if (res.ok) {
        const payload = await res.json();
        setActiveGrid(payload.data.timetable);
        setActiveGridId(id);
        setSelectedGridEntries(payload.data.timetable.entries || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const validateCellConflict = async () => {
    try {
      const res = await fetch('/api/v1/timetable/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timetableId: activeGridId,
          dayOfWeek: cellForm.dayOfWeek,
          timeSlotId: cellForm.timeSlotId,
          facultyId: cellForm.facultyId || null,
          roomId: cellForm.roomId || null,
          labId: cellForm.labId || null
        })
      });
      if (res.ok) {
        const payload = await res.json();
        setClashResults(payload.data.conflicts || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const saveCell = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/timetable/grids/${activeGridId}/entries`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(cellForm)
      });
      if (res.ok) {
        setOpenCellDialog(false);
        setCellForm({ dayOfWeek: 'MONDAY', timeSlotId: '', subjectId: '', facultyId: '', roomId: '', labId: '' });
        setClashResults([]);
        loadGridDetail(activeGridId);
      } else {
        const payload = await res.json();
        alert(payload.message || "Conflict check block prevented save.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSubstitutes = async () => {
    try {
      const res = await fetch('/api/v1/timetable/substitute');
      if (res.ok) {
        const payload = await res.json();
        setSubstitutes(payload.data.substitutes || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createSubstitute = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/timetable/substitute', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(subForm)
      });
      if (res.ok) {
        setSubForm({ date: '', timetableEntryId: '', substituteFacultyId: '' });
        fetchSubstitutes();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const approveSubstitute = async (id: string) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`/api/v1/timetable/substitute/${id}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchSubstitutes();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const submitApproval = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/timetable/approval', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(approveForm)
      });
      if (res.ok) {
        setOpenApproveDialog(false);
        setApproveForm({ timetableId: '', stage: 'MASTER_ADMIN', status: 'APPROVED', remarks: '' });
        fetchGrids();
        if (activeGridId) loadGridDetail(activeGridId);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadRoleSchedule = async () => {
    const token = localStorage.getItem('access_token');
    const endpoint = userRole === 'STUDENT' ? '/api/v1/timetable/student/schedule' : '/api/v1/timetable/faculty/schedule';
    try {
      const res = await fetch(endpoint, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        setRoleSchedule(payload.data.schedule || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchMetadata();
    fetchCalendar();
    fetchSlots();
    fetchGrids();
    fetchSubstitutes();
  }, []);

  useEffect(() => {
    if (userRole === 'STUDENT' || userRole === 'TEACHER') {
      loadRoleSchedule();
    }
  }, [userRole]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Helper to resolve cell content in weekly view grid
  const getCellEntry = (day: string, slotId: string) => {
    return selectedGridEntries.find(e => e.dayOfWeek === day && e.timeSlotId === slotId);
  };

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Page Header */}
      <Card sx={{ 
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', 
        color: '#f8fafc',
        borderRadius: 4, 
        mb: 4,
        boxShadow: '0 8px 20px rgba(15,23,42,0.2)'
      }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800 }}>
            🗓️ Smart Timetable Control Console
          </Typography>
          <Typography variant="subtitle1" sx={{ color: '#94a3b8', mt: 0.5, fontWeight: 500 }}>
            Institutional Schedule Coordination, Conflict Detection, and Substitutes Planning
          </Typography>
        </CardContent>
      </Card>

      {/* Role Schedules Check */}
      {(userRole === 'STUDENT' || userRole === 'TEACHER') && (
        <Paper sx={{ p: 4, borderRadius: 3, mb: 4 }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>
            📅 My Personal Timetable Grid
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Day</TableCell>
                  <TableCell>Period Slot</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>{userRole === 'STUDENT' ? 'Classroom Room' : 'Class Section'}</TableCell>
                  <TableCell>{userRole === 'STUDENT' ? 'Instructor' : 'Timings'}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {roleSchedule.map((row, idx) => (
                  <TableRow key={idx}>
                    <TableCell sx={{ fontWeight: '600' }}>{row.dayOfWeek}</TableCell>
                    <TableCell>{row.timeSlotName}</TableCell>
                    <TableCell>{row.subjectName || 'Break/Free'}</TableCell>
                    <TableCell>{userRole === 'STUDENT' ? row.roomNumber : row.sectionName}</TableCell>
                    <TableCell>{userRole === 'STUDENT' ? row.facultyName : `${row.startTime} - ${row.endTime}`}</TableCell>
                  </TableRow>
                ))}
                {roleSchedule.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} align="center">No active timetable sessions are currently scheduled.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Admin Panel */}
      {userRole === 'MASTER_ADMIN' && (
        <>
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange} sx={{ '& .MuiTab-root': { fontFamily: 'Outfit', fontWeight: 600 } }}>
              <Tab icon={<CalendarIcon />} iconPosition="start" label="Academic Calendar" />
              <Tab icon={<TimeIcon />} iconPosition="start" label="Period Manager" />
              <Tab icon={<GridIcon />} iconPosition="start" label="Timetable Editor" />
              <Tab icon={<SwapIcon />} iconPosition="start" label="Substitute Desk" />
            </Tabs>
          </Box>

          {/* 0. ACADEMIC CALENDAR */}
          {tabValue === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={5}>
                <Paper sx={{ p: 3, borderRadius: 3 }}>
                  <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📅 Calendar Configuration</Typography>
                  {calendar ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Alert severity="info">
                        Active Calendar Version: <strong>v{calendar.version}</strong>
                      </Alert>
                      <Typography variant="body2">
                        Working Days: {calendar.workingDays.join(', ')}
                      </Typography>
                      <Button variant="contained" onClick={() => setOpenEventDialog(true)}>Add Calendar Event</Button>
                    </Box>
                  ) : (
                    <Alert severity="warning">No calendar setup has been configured yet.</Alert>
                  )}
                </Paper>
              </Grid>
              <Grid item xs={12} md={7}>
                <Paper sx={{ p: 3, borderRadius: 3 }}>
                  <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📆 Calendar Events & Holidays</Typography>
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Event Title</TableCell>
                          <TableCell>Date</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell>Description</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {events.map((e) => (
                          <TableRow key={e.id}>
                            <TableCell sx={{ fontWeight: '600' }}>{e.title}</TableCell>
                            <TableCell>{new Date(e.eventDate).toLocaleDateString()}</TableCell>
                            <TableCell>
                              <Chip label={e.type} size="small" color={e.type === 'HOLIDAY' ? 'error' : 'primary'} />
                            </TableCell>
                            <TableCell>{e.description || '-'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>
            </Grid>
          )}

          {/* 1. PERIOD slot MANAGER */}
          {tabValue === 1 && (
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>🕰️ Period Slots Setup</Typography>
                <Button variant="contained" onClick={() => setOpenSlotDialog(true)}>Create Time Slot</Button>
              </Box>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Slot Name</TableCell>
                      <TableCell>Start Time</TableCell>
                      <TableCell>End Time</TableCell>
                      <TableCell>Type</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {slots.map((s) => (
                      <TableRow key={s.id}>
                        <TableCell sx={{ fontWeight: '600' }}>{s.name}</TableCell>
                        <TableCell>{s.startTime}</TableCell>
                        <TableCell>{s.endTime}</TableCell>
                        <TableCell>{s.type}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* 2. TIMETABLE WRITER GRID */}
          {tabValue === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 3, borderRadius: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>📂 Active Timetable Grids</Typography>
                    <Button variant="outlined" size="small" onClick={() => setOpenGridDialog(true)}>Add Header</Button>
                  </Box>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {grids.map((g) => (
                      <Paper 
                        key={g.id} 
                        variant="outlined" 
                        sx={{ 
                          p: 2, 
                          cursor: 'pointer',
                          borderColor: activeGridId === g.id ? 'primary.main' : '#e2e8f0',
                          bgcolor: activeGridId === g.id ? '#eff6ff' : '#fff'
                        }}
                        onClick={() => loadGridDetail(g.id)}
                      >
                        <Typography variant="subtitle2" fontWeight="700">{g.name}</Typography>
                        <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 0.5 }}>
                          Section: {g.section} • Semester {g.semester}
                        </Typography>
                        <Chip label={g.status} size="small" color={g.status === 'PUBLISHED' ? 'success' : 'warning'} sx={{ mt: 1 }} />
                      </Paper>
                    ))}
                  </Box>
                </Paper>
              </Grid>
              <Grid item xs={12} md={8}>
                {activeGrid ? (
                  <Paper sx={{ p: 3, borderRadius: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>🗓️ Grid Matrix Editor</Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button variant="outlined" color="success" onClick={() => setOpenApproveDialog(true)}>Approval Stages</Button>
                        <Button variant="contained" onClick={() => setOpenCellDialog(true)}>Assign Slot</Button>
                      </Box>
                    </Box>
                    <TableContainer sx={{ border: '1px solid #e2e8f0', borderRadius: 2 }}>
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>Day / Slot</TableCell>
                            {slots.map(s => (
                              <TableCell key={s.id} align="center">
                                <strong>{s.name}</strong><br />
                                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{s.startTime} - {s.endTime}</span>
                              </TableCell>
                            ))}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'].map(day => (
                            <TableRow key={day}>
                              <TableCell sx={{ fontWeight: '700' }}>{day}</TableCell>
                              {slots.map(slot => {
                                const cell = getCellEntry(day, slot.id);
                                return (
                                  <TableCell key={slot.id} align="center" sx={{ bgcolor: cell ? '#f0fdf4' : 'transparent' }}>
                                    {cell ? (
                                      <Box>
                                        <Typography variant="body2" fontWeight="700" color="primary.main">{cell.subjectName}</Typography>
                                        <Typography variant="caption" sx={{ display: 'block' }}>Room: {cell.roomNumber}</Typography>
                                        <Typography variant="caption" color="textSecondary">{cell.facultyName}</Typography>
                                      </Box>
                                    ) : (
                                      <Typography variant="caption" color="textSecondary">Free</Typography>
                                    )}
                                  </TableCell>
                                );
                              })}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Paper>
                ) : (
                  <Paper sx={{ p: 4, borderRadius: 3, textAlign: 'center' }}>
                    <Typography color="textSecondary">Select a timetable grid layout from the left to start editing.</Typography>
                  </Paper>
                )}
              </Grid>
            </Grid>
          )}

          {/* 3. SUBSTITUTE DESK */}
          {tabValue === 3 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={5}>
                <Paper sx={{ p: 3, borderRadius: 3 }}>
                  <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>🔀 New Swap Request</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                    <TextField 
                      label="Period Date" 
                      type="date" 
                      InputLabelProps={{ shrink: true }} 
                      fullWidth 
                      value={subForm.date} 
                      onChange={(e) => setSubForm({ ...subForm, date: e.target.value })} 
                    />
                    <TextField 
                      select 
                      label="Select Timetable Entry" 
                      fullWidth 
                      value={subForm.timetableEntryId} 
                      onChange={(e) => setSubForm({ ...subForm, timetableEntryId: e.target.value })}
                    >
                      {selectedGridEntries.map((e) => (
                        <MenuItem key={e.id} value={e.id}>
                          {e.dayOfWeek} - {e.timeSlotName}: {e.subjectName} ({e.facultyName})
                        </MenuItem>
                      ))}
                    </TextField>
                    <TextField 
                      select 
                      label="Substitute Instructor" 
                      fullWidth 
                      value={subForm.substituteFacultyId} 
                      onChange={(e) => setSubForm({ ...subForm, substituteFacultyId: e.target.value })}
                    >
                      {teachers.map((t) => (
                        <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>
                      ))}
                    </TextField>
                    <Button variant="contained" onClick={createSubstitute} disabled={!subForm.date || !subForm.timetableEntryId || !subForm.substituteFacultyId}>
                      Publish Swap
                    </Button>
                  </Box>
                </Paper>
              </Grid>
              <Grid item xs={12} md={7}>
                <Paper sx={{ p: 3, borderRadius: 3 }}>
                  <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>🔄 Swap Approvals Logs</Typography>
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Date</TableCell>
                          <TableCell>Subject</TableCell>
                          <TableCell>Original Faculty</TableCell>
                          <TableCell>Substitute Faculty</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell align="right">Action</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {substitutes.map((s) => (
                          <TableRow key={s.id}>
                            <TableCell>{new Date(s.date).toLocaleDateString()}</TableCell>
                            <TableCell sx={{ fontWeight: '600' }}>{s.subjectName}</TableCell>
                            <TableCell>{s.originalFaculty}</TableCell>
                            <TableCell>{s.substituteFaculty}</TableCell>
                            <TableCell>
                              <Chip label={s.status} size="small" color={s.status === 'APPROVED' ? 'success' : 'warning'} />
                            </TableCell>
                            <TableCell align="right">
                              {s.status === 'PENDING' && (
                                <Button size="small" variant="contained" color="success" onClick={() => approveSubstitute(s.id)}>
                                  Approve
                                </Button>
                              )}
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
        </>
      )}

      {/* DIALOGS */}
      {/* Event Dialog */}
      <Dialog open={openEventDialog} onClose={() => setOpenEventDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Add Calendar Event</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            label="Event Title" 
            fullWidth 
            value={eventForm.title} 
            onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })} 
          />
          <TextField 
            label="Event Date" 
            type="date" 
            InputLabelProps={{ shrink: true }} 
            fullWidth 
            value={eventForm.eventDate} 
            onChange={(e) => setEventForm({ ...eventForm, eventDate: e.target.value })} 
          />
          <TextField 
            select 
            label="Event Type" 
            fullWidth 
            value={eventForm.type} 
            onChange={(e) => setEventForm({ ...eventForm, type: e.target.value })}
          >
            <MenuItem value="HOLIDAY">Government Holiday</MenuItem>
            <MenuItem value="EXAM_DAY">Examination Session Day</MenuItem>
            <MenuItem value="COLLEGE_EVENT">Institutional Event Day</MenuItem>
            <MenuItem value="SPECIAL_WORKING_DAY">Special Working Saturday</MenuItem>
          </TextField>
          <TextField 
            label="Description" 
            multiline 
            rows={2} 
            fullWidth 
            value={eventForm.description} 
            onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEventDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={createEvent}>Add Event</Button>
        </DialogActions>
      </Dialog>

      {/* Slot Dialog */}
      <Dialog open={openSlotDialog} onClose={() => setOpenSlotDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Create Time Slot</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          {slotError && <Alert severity="error">{slotError}</Alert>}
          <TextField 
            label="Slot Name (e.g. Period 1)" 
            fullWidth 
            value={slotForm.name} 
            onChange={(e) => setSlotForm({ ...slotForm, name: e.target.value })} 
          />
          <TextField 
            label="Start Timings" 
            type="time" 
            InputLabelProps={{ shrink: true }} 
            fullWidth 
            value={slotForm.startTime} 
            onChange={(e) => setSlotForm({ ...slotForm, startTime: e.target.value })} 
          />
          <TextField 
            label="End Timings" 
            type="time" 
            InputLabelProps={{ shrink: true }} 
            fullWidth 
            value={slotForm.endTime} 
            onChange={(e) => setSlotForm({ ...slotForm, endTime: e.target.value })} 
          />
          <TextField 
            select 
            label="Slot Category" 
            fullWidth 
            value={slotForm.type} 
            onChange={(e) => setSlotForm({ ...slotForm, type: e.target.value })}
          >
            <MenuItem value="CLASS">Standard Lecture Class</MenuItem>
            <MenuItem value="BREAK">Recreation/Lunch Break</MenuItem>
            <MenuItem value="LAB">Department Lab Slot</MenuItem>
            <MenuItem value="EXTRA">Remedial Extra Class</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSlotDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={createSlot}>Save Slot</Button>
        </DialogActions>
      </Dialog>

      {/* Grid Dialog */}
      <Dialog open={openGridDialog} onClose={() => setOpenGridDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Create Timetable Header</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            label="Layout Name (e.g. Section A Term 3)" 
            fullWidth 
            value={gridForm.name} 
            onChange={(e) => setGridForm({ ...gridForm, name: e.target.value })} 
          />
          <TextField 
            select 
            label="Academic Year" 
            fullWidth 
            value={gridForm.academicYearId} 
            onChange={(e) => setGridForm({ ...gridForm, academicYearId: e.target.value })}
          >
            {academicYears.map((ay) => (
              <MenuItem key={ay.id} value={ay.id}>{ay.name}</MenuItem>
            ))}
          </TextField>
          <TextField 
            select 
            label="Semester" 
            fullWidth 
            value={gridForm.semesterId} 
            onChange={(e) => setGridForm({ ...gridForm, semesterId: e.target.value })}
          >
            {semesters.map((sem) => (
              <MenuItem key={sem.id} value={sem.id}>Semester {sem.semesterNumber}</MenuItem>
            ))}
          </TextField>
          <TextField 
            select 
            label="Class Section" 
            fullWidth 
            value={gridForm.sectionId} 
            onChange={(e) => setGridForm({ ...gridForm, sectionId: e.target.value })}
          >
            {sections.map((s) => (
              <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenGridDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={createGrid}>Add Grid</Button>
        </DialogActions>
      </Dialog>

      {/* Cell Assign Dialog */}
      <Dialog open={openCellDialog} onClose={() => setOpenCellDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Assign Period Slot</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          {clashResults.length > 0 ? (
            <Alert severity="error" icon={<WarningIcon />}>
              <strong>Conflict clashes detected!</strong>
              <ul style={{ margin: '8px 0 0 16px', padding: 0 }}>
                {clashResults.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </Alert>
          ) : (
            cellForm.timeSlotId && <Alert severity="success" icon={<CheckIcon />}>Slot parameters are safe to assign.</Alert>
          )}

          <TextField 
            select 
            label="Day of Week" 
            fullWidth 
            value={cellForm.dayOfWeek} 
            onChange={(e) => setCellForm({ ...cellForm, dayOfWeek: e.target.value })}
          >
            {['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'].map(d => (
              <MenuItem key={d} value={d}>{d}</MenuItem>
            ))}
          </TextField>
          <TextField 
            select 
            label="Select Time Slot" 
            fullWidth 
            value={cellForm.timeSlotId} 
            onChange={(e) => setCellForm({ ...cellForm, timeSlotId: e.target.value })}
          >
            {slots.map((s) => (
              <MenuItem key={s.id} value={s.id}>{s.name} ({s.startTime} - {s.endTime})</MenuItem>
            ))}
          </TextField>
          <TextField 
            select 
            label="Subject" 
            fullWidth 
            value={cellForm.subjectId} 
            onChange={(e) => setCellForm({ ...cellForm, subjectId: e.target.value })}
          >
            <MenuItem value=""><em>None (Break/Free Slot)</em></MenuItem>
            {subjects.map((sub) => (
              <MenuItem key={sub.id} value={sub.id}>{sub.name}</MenuItem>
            ))}
          </TextField>
          <TextField 
            select 
            label="Assign Teacher" 
            fullWidth 
            value={cellForm.facultyId} 
            onChange={(e) => setCellForm({ ...cellForm, facultyId: e.target.value })}
          >
            <MenuItem value=""><em>None</em></MenuItem>
            {teachers.map((t) => (
              <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>
            ))}
          </TextField>
          <TextField 
            select 
            label="Assign Classroom Room" 
            fullWidth 
            value={cellForm.roomId} 
            onChange={(e) => setCellForm({ ...cellForm, roomId: e.target.value })}
          >
            <MenuItem value=""><em>None</em></MenuItem>
            {rooms.map((r) => (
              <MenuItem key={r.id} value={r.id}>{r.roomNumber}</MenuItem>
            ))}
          </TextField>
          <TextField 
            select 
            label="Assign Laboratory (Lab)" 
            fullWidth 
            value={cellForm.labId} 
            onChange={(e) => setCellForm({ ...cellForm, labId: e.target.value })}
          >
            <MenuItem value=""><em>None</em></MenuItem>
            {labs.map((l) => (
              <MenuItem key={l.id} value={l.id}>{l.labName}</MenuItem>
            ))}
          </TextField>

          <Button variant="outlined" color="warning" onClick={validateCellConflict} disabled={!cellForm.timeSlotId}>
            Run Conflict Check
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCellDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={saveCell} disabled={!cellForm.timeSlotId}>Save Cell</Button>
        </DialogActions>
      </Dialog>

      {/* Timetable Approval Dialog */}
      <Dialog open={openApproveDialog} onClose={() => setOpenApproveDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>Review Approval Stages</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          <TextField 
            select 
            label="Workflow Approval Stage" 
            fullWidth 
            value={approveForm.stage} 
            onChange={(e) => setApproveForm({ ...approveForm, stage: e.target.value })}
          >
            <MenuItem value="DEPT_REVIEW">Department Stage Review</MenuItem>
            <MenuItem value="ACADEMIC_OFFICE">Academic Office Review</MenuItem>
            <MenuItem value="MASTER_ADMIN">Master Admin Final Approval</MenuItem>
          </TextField>
          <TextField 
            select 
            label="Action Status" 
            fullWidth 
            value={approveForm.status} 
            onChange={(e) => setApproveForm({ ...approveForm, status: e.target.value })}
          >
            <MenuItem value="APPROVED">Approve and Progress</MenuItem>
            <MenuItem value="REJECTED">Reject / Revision Required</MenuItem>
          </TextField>
          <TextField 
            label="Remarks / Feedback Comments" 
            multiline 
            rows={2} 
            fullWidth 
            value={approveForm.remarks} 
            onChange={(e) => setApproveForm({ ...approveForm, remarks: e.target.value })} 
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenApproveDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => {
            approveForm.timetableId = activeGridId;
            submitApproval();
          }}>Submit Stage Log</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TimetableDashboard;
