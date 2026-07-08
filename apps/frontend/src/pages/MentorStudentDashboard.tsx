import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button, LinearProgress, TextField, Chip
} from '@mui/material';
import { Search } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import AcademicMentorDisclaimer from '../components/AcademicMentorDisclaimer';

export const MentorStudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchStudents = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/api/v1/academic-mentor/students', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.success) {
          setStudents(payload.data || []);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return '#4caf50';
      case 'MODERATE': return '#ff9800';
      case 'HIGH': return '#f44336';
      case 'CRITICAL': return '#b71c1c';
      default: return '#757575';
    }
  };

  const filtered = students.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.email.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography mt={2}>Loading Student Risk Directory...</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight="bold" color="primary" gutterBottom>
        Teacher Mentoring Directory
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Monitor risk trends, academic completeness indicators, and assign support interventions to students in your sections.
      </Typography>

      <Box my={3} display="flex" gap={2}>
        <TextField
          label="Search Students"
          variant="outlined"
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{ endAdornment: <Search /> }}
          sx={{ width: 300 }}
        />
      </Box>

      {filtered.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">No students found matching search criteria.</Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Student Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Section</TableCell>
                <TableCell align="right">Advisory Risk Level</TableCell>
                <TableCell align="right">Risk Score (0-100)</TableCell>
                <TableCell align="right">Data Completeness</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.map((s) => (
                <TableRow key={s.id}>
                  <TableCell sx={{ fontWeight: '600' }}>{s.name}</TableCell>
                  <TableCell>{s.email}</TableCell>
                  <TableCell>{s.sectionId || 'Unassigned'}</TableCell>
                  <TableCell align="right">
                    <Chip
                      label={s.riskLevel}
                      style={{
                        backgroundColor: getRiskColor(s.riskLevel) + '22',
                        color: getRiskColor(s.riskLevel),
                        fontWeight: 'bold'
                      }}
                    />
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                    {s.riskLevel === 'INSUFFICIENT_DATA' ? 'N/A' : s.riskScore}
                  </TableCell>
                  <TableCell align="right">
                    <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
                      <Typography variant="body2">{s.dataCompleteness}%</Typography>
                      <Box width={60}>
                        <LinearProgress variant="determinate" value={s.dataCompleteness} />
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => navigate(`/mentor/students`, { state: { targetStudentId: s.id } })}
                      sx={{ mr: 1 }}
                    >
                      Assess
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => navigate('/mentor/interventions', { state: { studentId: s.id, studentName: s.name } })}
                    >
                      Intervene
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <AcademicMentorDisclaimer />
    </Box>
  );
};
export default MentorStudentDashboard;
