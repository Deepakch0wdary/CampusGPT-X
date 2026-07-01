import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  TextField, 
  MenuItem, 
  Grid,
  Card,
  CardContent,
  Alert,
  LinearProgress
} from '@mui/material';
import { 
  QrCode2 as QrIcon, 
  LocationOn as GeoIcon, 
  TimerOutlined as TimerIcon
} from '@mui/icons-material';

export const QRAttendanceDashboard: React.FC = () => {
  const [userRole, setUserRole] = useState<string>('STUDENT');
  const [activeTab, setActiveTab] = useState<'FACULTY' | 'STUDENT'>('STUDENT');

  // Metadata Lists
  const [academicYears, setAcademicYears] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [programs, setPrograms] = useState<any[]>([]);
  const [semesters, setSemesters] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [slots, setSlots] = useState<any[]>([]);

  // Geofencing Coordinates State
  const [coords, setCoords] = useState<{ latitude: number; longitude: number }>({ latitude: 12.9716, longitude: 77.5946 });

  // Faculty QR Session
  const [sessionForm, setSessionForm] = useState({
    academicYearId: '',
    departmentId: '',
    programId: '',
    semesterId: '',
    sectionId: '',
    subjectId: '',
    timeSlotId: '',
    date: new Date().toISOString().split('T')[0],
    latitude: 12.9716,
    longitude: 77.5946,
    allowedRadius: 100,
    intervalSeconds: 30
  });

  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [activeCode, setActiveCode] = useState<string>('');
  const [remainingTime, setRemainingTime] = useState<number>(30);
  const [liveStats, setLiveStats] = useState<any>(null);

  // Student Scan Form
  const [studentScanForm, setStudentScanForm] = useState({
    qrSessionId: '',
    scannedToken: '',
    latitude: 12.9716,
    longitude: 77.5946,
    deviceId: ''
  });
  const [scanResult, setScanResult] = useState<{ success: boolean; message: string } | null>(null);

  const fetchMetadata = async () => {
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const u = JSON.parse(userStr);
      const role = u.role || 'STUDENT';
      setUserRole(role);
      setActiveTab(role === 'STUDENT' ? 'STUDENT' : 'FACULTY');
    }

    try {
      const resAy = await fetch('/api/v1/academic-years', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resAy.ok) {
        const p = await resAy.json();
        setAcademicYears(p.data || []);
      }
      const resDept = await fetch('/api/v1/departments', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resDept.ok) {
        const p = await resDept.json();
        setDepartments(p.data || []);
      }
      const resProg = await fetch('/api/v1/programs', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resProg.ok) {
        const p = await resProg.json();
        setPrograms(p.data || []);
      }
      const resSem = await fetch('/api/v1/semesters', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSem.ok) {
        const p = await resSem.json();
        setSemesters(p.data || []);
      }
      const resSec = await fetch('/api/v1/sections', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSec.ok) {
        const p = await resSec.json();
        setSections(p.data || []);
      }
      const resSub = await fetch('/api/v1/subjects', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSub.ok) {
        const p = await resSub.json();
        setSubjects(p.data || []);
      }
      const resSlots = await fetch('/api/v1/timetable/slots', { headers: { 'Authorization': `Bearer ${token}` } });
      if (resSlots.ok) {
        const p = await resSlots.json();
        setSlots(p.data.slots || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getGeolocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const c = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
          setCoords(c);
          setSessionForm(prev => ({ ...prev, latitude: c.latitude, longitude: c.longitude }));
          setStudentScanForm(prev => ({ ...prev, latitude: c.latitude, longitude: c.longitude }));
        },
        (err) => console.warn(err)
      );
    }
  };

  const startQR = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/qr-attendance/session', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...sessionForm,
          timeSlotId: sessionForm.timeSlotId || null,
          date: new Date(sessionForm.date).toISOString()
        })
      });
      if (res.ok) {
        const payload = await res.json();
        setActiveSessionId(payload.data.id);
        setActiveCode(payload.data.code);
        setRemainingTime(sessionForm.intervalSeconds);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const closeQR = async () => {
    const token = localStorage.getItem('access_token');
    if (!activeSessionId) return;
    try {
      const res = await fetch(`/api/v1/qr-attendance/session/${activeSessionId}/close`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setActiveSessionId('');
        setActiveCode('');
        setLiveStats(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const pollCodeAndStats = async () => {
    if (!activeSessionId) return;
    const token = localStorage.getItem('access_token');
    try {
      const resCode = await fetch(`/api/v1/qr-attendance/session/${activeSessionId}/code`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resCode.ok) {
        const p = await resCode.json();
        setActiveCode(p.data.code);
        setRemainingTime(p.data.remainingSeconds);
      }
      
      const resStats = await fetch(`/api/v1/qr-attendance/session/${activeSessionId}/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resStats.ok) {
        const p = await resStats.json();
        setLiveStats(p.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const submitScan = async () => {
    const token = localStorage.getItem('access_token');
    setScanResult(null);
    try {
      // Auto-populate random device ID if empty for demonstration
      const deviceId = studentScanForm.deviceId || 'device-' + Math.random().toString(36).substr(2, 9);
      const res = await fetch('/api/v1/qr-attendance/scan', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...studentScanForm,
          deviceId
        })
      });
      const payload = await res.json();
      if (res.ok) {
        setScanResult({ success: true, message: payload.message });
      } else {
        setScanResult({ success: false, message: payload.message || "Failed to scan." });
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchMetadata();
    getGeolocation();
  }, []);

  // Poll active QR Session codes and stats every 3 seconds
  useEffect(() => {
    if (!activeSessionId) return;
    pollCodeAndStats();
    const interval = setInterval(() => {
      pollCodeAndStats();
    }, 3000);
    return () => clearInterval(interval);
  }, [activeSessionId]);

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Premium Header Banner */}
      <Card sx={{ 
        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 
        color: '#f8fafc',
        borderRadius: 4, 
        mb: 4,
        boxShadow: '0 8px 24px rgba(5,150,105,0.25)'
      }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800 }}>
            ⚡ Dynamic QR Attendance Console
          </Typography>
          <Typography variant="subtitle1" sx={{ color: '#d1fae5', mt: 0.5, fontWeight: 500 }}>
            Geofence Validations, Anti-Proxy Device Identity Checking, and Real-Time Countdown Timers
          </Typography>
        </CardContent>
      </Card>

      {/* Renders Location Badge */}
      <Alert icon={<GeoIcon />} severity="info" sx={{ mb: 4, borderRadius: 3 }}>
        Your Current Coordinates: <strong>Lat: {coords.latitude.toFixed(6)}</strong>, <strong>Lon: {coords.longitude.toFixed(6)}</strong>
      </Alert>

      {/* Role Selection Tabs */}
      {userRole !== 'STUDENT' && (
        <Box sx={{ mb: 3 }}>
          <Button 
            variant={activeTab === 'FACULTY' ? 'contained' : 'outlined'} 
            onClick={() => setActiveTab('FACULTY')} 
            sx={{ mr: 1 }}
          >
            Faculty Dashboard
          </Button>
          <Button 
            variant={activeTab === 'STUDENT' ? 'contained' : 'outlined'} 
            onClick={() => setActiveTab('STUDENT')}
          >
            Student scanner Panel
          </Button>
        </Box>
      )}

      {/* 1. FACULTY QR GENERATOR PANEL */}
      {activeTab === 'FACULTY' && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={5}>
            <Paper sx={{ p: 3, borderRadius: 3 }}>
              <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>🚀 Launch QR Session</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
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
                  {semesters.map((s) => <MenuItem key={s.id} value={s.id}>Semester {s.semesterNumber}</MenuItem>)}
                </TextField>
                <TextField 
                  select 
                  label="Section" 
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
                  label="Timetable Slot" 
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
                
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField 
                      select 
                      label="Allowed Radius (m)" 
                      fullWidth 
                      value={sessionForm.allowedRadius} 
                      onChange={(e) => setSessionForm({ ...sessionForm, allowedRadius: Number(e.target.value) })}
                    >
                      <MenuItem value={50}>50 Meters</MenuItem>
                      <MenuItem value={100}>100 Meters</MenuItem>
                      <MenuItem value={200}>200 Meters</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid item xs={6}>
                    <TextField 
                      select 
                      label="Refresh Timer" 
                      fullWidth 
                      value={sessionForm.intervalSeconds} 
                      onChange={(e) => setSessionForm({ ...sessionForm, intervalSeconds: Number(e.target.value) })}
                    >
                      <MenuItem value={30}>30 Seconds</MenuItem>
                      <MenuItem value={45}>45 Seconds</MenuItem>
                      <MenuItem value={60}>60 Seconds</MenuItem>
                    </TextField>
                  </Grid>
                </Grid>

                <Button 
                  variant="contained" 
                  size="large" 
                  onClick={startQR} 
                  disabled={!sessionForm.sectionId || !sessionForm.subjectId || !!activeSessionId}
                >
                  Generate Dynamic QR
                </Button>
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={7}>
            {activeSessionId ? (
              <Paper sx={{ p: 4, borderRadius: 3, textAlign: 'center' }}>
                <Typography variant="h5" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 1 }}>📲 Dynamic Access Key</Typography>
                <Box sx={{ my: 4, display: 'inline-flex', p: 4, border: '4px solid #10b981', borderRadius: 4, bgcolor: '#f0fdf4' }}>
                  {/* Mocked QR representation card containing active CodeValue */}
                  <Box sx={{ width: 220, height: 220, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', bgcolor: '#fff', border: '1px dashed #059669', p: 2 }}>
                    <QrIcon sx={{ fontSize: 100, color: 'primary.main' }} />
                    <Typography variant="caption" sx={{ mt: 2, wordBreak: 'break-all', fontFamily: 'monospace', fontWeight: 'bold' }}>
                      Token: {activeCode}
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ maxSquare: 400, mx: 'auto', mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                    <TimerIcon fontSize="small" /> Code expires in: <strong>{remainingTime}s</strong>
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(remainingTime / sessionForm.intervalSeconds) * 100} 
                    sx={{ height: 8, borderRadius: 4 }} 
                  />
                </Box>

                {liveStats && (
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={4}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="h6" fontWeight="800" color="success.main">{liveStats.presentCount}</Typography>
                        <Typography variant="caption" color="textSecondary">Students Present</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={4}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="h6" fontWeight="800" color="warning.main">{liveStats.pendingCount}</Typography>
                        <Typography variant="caption" color="textSecondary">Pending Scan</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={4}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="h6" fontWeight="800" color="primary.main">{liveStats.attendancePercentage.toFixed(0)}%</Typography>
                        <Typography variant="caption" color="textSecondary">Percentage</Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                )}

                <Button variant="contained" color="error" size="large" onClick={closeQR}>
                  Close Session
                </Button>
              </Paper>
            ) : (
              <Paper sx={{ p: 4, borderRadius: 3, textAlign: 'center', minHeight: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Typography color="textSecondary">Launch a session from the left column to generate a live QR matrix.</Typography>
              </Paper>
            )}
          </Grid>
        </Grid>
      )}

      {/* 2. STUDENT SCANNER PANEL */}
      {activeTab === 'STUDENT' && (
        <Paper sx={{ p: 4, borderRadius: 3, maxWidth: 600, mx: 'auto' }}>
          <Typography variant="h6" sx={{ fontFamily: 'Outfit', fontWeight: 700, mb: 2 }}>📸 Scan QR Code Access</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {scanResult && (
              <Alert severity={scanResult.success ? 'success' : 'error'}>
                {scanResult.message}
              </Alert>
            )}

            <TextField 
              label="Active QR Session ID" 
              placeholder="Paste generated QR Session ID"
              fullWidth 
              value={studentScanForm.qrSessionId}
              onChange={(e) => setStudentScanForm({ ...studentScanForm, qrSessionId: e.target.value })}
            />
            <TextField 
              label="Scanned Token Access Code" 
              placeholder="Paste active token code"
              fullWidth 
              value={studentScanForm.scannedToken}
              onChange={(e) => setStudentScanForm({ ...studentScanForm, scannedToken: e.target.value })}
            />
            <TextField 
              label="Browser Device Fingerprint ID (Optional)" 
              placeholder="Unique Phone/Computer signature ID"
              fullWidth 
              value={studentScanForm.deviceId}
              onChange={(e) => setStudentScanForm({ ...studentScanForm, deviceId: e.target.value })}
            />

            <Button 
              variant="contained" 
              size="large" 
              color="success" 
              onClick={submitScan} 
              disabled={!studentScanForm.qrSessionId || !studentScanForm.scannedToken}
            >
              Verify & Register Attendance
            </Button>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default QRAttendanceDashboard;
