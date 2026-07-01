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
  TablePagination, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  TextField, 
  MenuItem, 
  FormControlLabel, 
  Checkbox, 
  IconButton
} from '@mui/material';
import { 
  Add as AddIcon, 
  Edit as EditIcon, 
  Delete as DeleteIcon, 
  Refresh as RefreshIcon
} from '@mui/icons-material';

export const AcademicDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [userRole, setUserRole] = useState<string>('STUDENT');

  // Lists
  const [academicYears, setAcademicYears] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [programs, setPrograms] = useState<any[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [semesters, setSemesters] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [buildings, setBuildings] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [laboratories, setLaboratories] = useState<any[]>([]);
  const [facultyAssignments, setFacultyAssignments] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);

  // Pagination & Search
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);

  // Dialog State
  const [openDialog, setOpenDialog] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [formData, setFormData] = useState<any>({});

  const loadRole = () => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const u = JSON.parse(userStr);
        setUserRole(u.role || 'STUDENT');
      } catch {
        setUserRole('STUDENT');
      }
    }
  };

  const getApiUrl = (tab: number) => {
    switch (tab) {
      case 0: return '/api/v1/academic-years';
      case 1: return '/api/v1/departments';
      case 2: return '/api/v1/programs';
      case 3: return '/api/v1/courses';
      case 4: return '/api/v1/semesters';
      case 5: return '/api/v1/subjects';
      case 6: return '/api/v1/sections';
      case 7: return '/api/v1/buildings';
      case 8: return '/api/v1/rooms';
      case 9: return '/api/v1/laboratories';
      case 10: return '/api/v1/faculty-assignments';
      default: return '';
    }
  };

  const getApiKey = (tab: number) => {
    switch (tab) {
      case 0: return 'academic_years';
      case 1: return 'departments';
      case 2: return 'programs';
      case 3: return 'courses';
      case 4: return 'semesters';
      case 5: return 'subjects';
      case 6: return 'sections';
      case 7: return 'buildings';
      case 8: return 'rooms';
      case 9: return 'laboratories';
      case 10: return 'assignments';
      default: return '';
    }
  };

  const fetchData = async () => {
    const token = localStorage.getItem('access_token');
    const url = `${getApiUrl(tabValue)}?search=${search}&page=${page + 1}&limit=${rowsPerPage}`;
    try {
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        const key = getApiKey(tabValue);
        if (payload.success && payload.data) {
          const list = payload.data[key] || [];
          setTotalItems(payload.data.total || list.length);
          
          switch (tabValue) {
            case 0: setAcademicYears(list); break;
            case 1: setDepartments(list); break;
            case 2: setPrograms(list); break;
            case 3: setCourses(list); break;
            case 4: setSemesters(list); break;
            case 5: setSubjects(list); break;
            case 6: setSections(list); break;
            case 7: setBuildings(list); break;
            case 8: setRooms(list); break;
            case 9: setLaboratories(list); break;
            case 10: setFacultyAssignments(list); break;
          }
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Helper fetch to resolve select options
  const fetchAuxiliary = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const endpoints = [
        '/api/v1/departments?limit=100',
        '/api/v1/programs?limit=100',
        '/api/v1/academic-years?limit=100',
        '/api/v1/courses?limit=100',
        '/api/v1/semesters?limit=100',
        '/api/v1/sections?limit=100',
        '/api/v1/subjects?limit=100',
        '/api/v1/buildings?limit=100',
        '/api/v1/users?limit=100'
      ];
      const responses = await Promise.all(
        endpoints.map(ep => fetch(ep, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()))
      );
      
      if (responses[0].success) setDepartments(responses[0].data.departments || []);
      if (responses[1].success) setPrograms(responses[1].data.programs || []);
      if (responses[2].success) setAcademicYears(responses[2].data.academic_years || []);
      if (responses[3].success) setCourses(responses[3].data.courses || []);
      if (responses[4].success) setSemesters(responses[4].data.semesters || []);
      if (responses[5].success) setSections(responses[5].data.sections || []);
      if (responses[6].success) setSubjects(responses[6].data.subjects || []);
      if (responses[7].success) setBuildings(responses[7].data.buildings || []);
      
      if (responses[8].success) {
        const allUsers = responses[8].data.users || [];
        setTeachers(allUsers.filter((u: any) => u.role === 'TEACHER'));
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadRole();
    fetchAuxiliary();
  }, []);

  useEffect(() => {
    fetchData();
  }, [tabValue, page, rowsPerPage, search]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setPage(0);
    setSearch('');
  };

  const handleOpenAdd = () => {
    setEditId(null);
    setFormData({});
    setOpenDialog(true);
  };

  const handleOpenEdit = (item: any) => {
    setEditId(item.id);
    setFormData({ ...item });
    setOpenDialog(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this resource?")) return;
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`${getApiUrl(tabValue)}/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchData();
        fetchAuxiliary();
      } else {
        const payload = await res.json();
        alert(payload.message || "Failed to delete.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSave = async () => {
    const token = localStorage.getItem('access_token');
    const method = editId ? 'PUT' : 'POST';
    const url = editId ? `${getApiUrl(tabValue)}/${editId}` : getApiUrl(tabValue);
    try {
      const res = await fetch(url, {
        method,
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setOpenDialog(false);
        fetchData();
        fetchAuxiliary();
      } else {
        const payload = await res.json();
        alert(payload.message || "Error saving record.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const isAdmin = userRole === 'MASTER_ADMIN';

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800 }}>
          Academic Administration
        </Typography>
        {isAdmin && (
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={handleOpenAdd}
            sx={{ bgcolor: 'primary.main', '&:hover': { bgcolor: 'primary.dark' } }}
          >
            Create Record
          </Button>
        )}
      </Box>

      <Paper sx={{ mb: 4, bgcolor: 'background.paper', borderRadius: 2 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="scrollable"
          scrollButtons="auto"
          textColor="primary"
          indicatorColor="primary"
          sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}
        >
          <Tab label="Academic Years" />
          <Tab label="Departments" />
          <Tab label="Programs" />
          <Tab label="Courses" />
          <Tab label="Semesters" />
          <Tab label="Subjects" />
          <Tab label="Sections" />
          <Tab label="Buildings" />
          <Tab label="Rooms" />
          <Tab label="Laboratories" />
          <Tab label="Faculty Assignments" />
        </Tabs>

        {/* SEARCH & FILTERS */}
        <Box sx={{ p: 3, display: 'flex', gap: 2 }}>
          <TextField
            label="Search Records..."
            variant="outlined"
            size="small"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ maxWidth: 300 }}
          />
          <IconButton onClick={fetchData} color="primary">
            <RefreshIcon />
          </IconButton>
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                {tabValue === 0 && (
                  <>
                    <TableCell>Name</TableCell>
                    <TableCell>Start Date</TableCell>
                    <TableCell>End Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Current</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 1 && (
                  <>
                    <TableCell>Name</TableCell>
                    <TableCell>Code</TableCell>
                    <TableCell>Dean/HOD</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Building</TableCell>
                    <TableCell>Status</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 2 && (
                  <>
                    <TableCell>Name</TableCell>
                    <TableCell>Code</TableCell>
                    <TableCell>Department</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 3 && (
                  <>
                    <TableCell>Code</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Credits</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>Program</TableCell>
                    <TableCell>Status</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 4 && (
                  <>
                    <TableCell>Semester #</TableCell>
                    <TableCell>Academic Year</TableCell>
                    <TableCell>Program</TableCell>
                    <TableCell>Start Date</TableCell>
                    <TableCell>End Date</TableCell>
                    <TableCell>Current</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 5 && (
                  <>
                    <TableCell>Code</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Credits</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Department</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 6 && (
                  <>
                    <TableCell>Name</TableCell>
                    <TableCell>Capacity</TableCell>
                    <TableCell>Semester</TableCell>
                    <TableCell>Department</TableCell>
                    <TableCell>Advisor</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 7 && (
                  <>
                    <TableCell>Name</TableCell>
                    <TableCell>Code</TableCell>
                    <TableCell>Floors</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 8 && (
                  <>
                    <TableCell>Room #</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Capacity</TableCell>
                    <TableCell>Building</TableCell>
                    <TableCell>Floor</TableCell>
                    <TableCell>Status</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 9 && (
                  <>
                    <TableCell>Lab Name</TableCell>
                    <TableCell>Department</TableCell>
                    <TableCell>Capacity</TableCell>
                    <TableCell>Systems</TableCell>
                    <TableCell>Assistant</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
                {tabValue === 10 && (
                  <>
                    <TableCell>Faculty</TableCell>
                    <TableCell>Subject</TableCell>
                    <TableCell>Section</TableCell>
                    <TableCell>Semester</TableCell>
                    <TableCell>Academic Year</TableCell>
                    {isAdmin && <TableCell align="right">Actions</TableCell>}
                  </>
                )}
              </TableRow>
            </TableHead>
            <TableBody>
              {tabValue === 0 && academicYears.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{new Date(item.startDate).toLocaleDateString()}</TableCell>
                  <TableCell>{new Date(item.endDate).toLocaleDateString()}</TableCell>
                  <TableCell>{item.status}</TableCell>
                  <TableCell>{item.currentAcademicYear ? "Yes" : "No"}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 1 && departments.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.code}</TableCell>
                  <TableCell>{item.deanHod}</TableCell>
                  <TableCell>{item.email}</TableCell>
                  <TableCell>{item.building}</TableCell>
                  <TableCell>{item.status}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 2 && programs.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.code}</TableCell>
                  <TableCell>{item.departmentName}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 3 && courses.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.code}</TableCell>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.credits}</TableCell>
                  <TableCell>{item.duration}</TableCell>
                  <TableCell>{item.programName}</TableCell>
                  <TableCell>{item.status}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 4 && semesters.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.semesterNumber}</TableCell>
                  <TableCell>{item.academicYearName}</TableCell>
                  <TableCell>{item.programName}</TableCell>
                  <TableCell>{new Date(item.startDate).toLocaleDateString()}</TableCell>
                  <TableCell>{new Date(item.endDate).toLocaleDateString()}</TableCell>
                  <TableCell>{item.currentSemester ? "Yes" : "No"}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 5 && subjects.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.code}</TableCell>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.credits}</TableCell>
                  <TableCell>{item.mandatory ? "Mandatory" : "Elective"}</TableCell>
                  <TableCell>{item.departmentName}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 6 && sections.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.capacity}</TableCell>
                  <TableCell>{item.semesterNumber}</TableCell>
                  <TableCell>{item.departmentName}</TableCell>
                  <TableCell>{item.facultyAdvisorName}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 7 && buildings.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.code}</TableCell>
                  <TableCell>{item.floors}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 8 && rooms.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.roomNumber}</TableCell>
                  <TableCell>{item.roomType}</TableCell>
                  <TableCell>{item.capacity}</TableCell>
                  <TableCell>{item.buildingName}</TableCell>
                  <TableCell>{item.floor}</TableCell>
                  <TableCell>{item.status}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 9 && laboratories.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.labName}</TableCell>
                  <TableCell>{item.departmentName}</TableCell>
                  <TableCell>{item.capacity}</TableCell>
                  <TableCell>{item.systems}</TableCell>
                  <TableCell>{item.labAssistant}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleOpenEdit(item)} color="primary"><EditIcon /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
              {tabValue === 10 && facultyAssignments.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.facultyName}</TableCell>
                  <TableCell>{item.subjectName}</TableCell>
                  <TableCell>{item.sectionName}</TableCell>
                  <TableCell>{item.semesterNumber}</TableCell>
                  <TableCell>{item.academicYearName}</TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><DeleteIcon /></IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={totalItems}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={(_e, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => setRowsPerPage(parseInt(e.target.value, 10))}
        />
      </Paper>

      {/* DYNAMIC EDIT/CREATE DIALOG */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontFamily: 'Outfit', fontWeight: 700 }}>
          {editId ? "Modify Record" : "Add Record"}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
            {tabValue === 0 && (
              <>
                <TextField label="Name" fullWidth value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
                <TextField label="Start Date" type="date" InputLabelProps={{ shrink: true }} fullWidth value={formData.startDate?.split('T')[0] || ''} onChange={(e) => setFormData({ ...formData, startDate: e.target.value })} />
                <TextField label="End Date" type="date" InputLabelProps={{ shrink: true }} fullWidth value={formData.endDate?.split('T')[0] || ''} onChange={(e) => setFormData({ ...formData, endDate: e.target.value })} />
                <TextField select label="Status" fullWidth value={formData.status || 'ACTIVE'} onChange={(e) => setFormData({ ...formData, status: e.target.value })}>
                  <MenuItem value="ACTIVE">ACTIVE</MenuItem>
                  <MenuItem value="INACTIVE">INACTIVE</MenuItem>
                </TextField>
                <FormControlLabel control={<Checkbox checked={!!formData.currentAcademicYear} onChange={(e) => setFormData({ ...formData, currentAcademicYear: e.target.checked })} />} label="Current Academic Year" />
              </>
            )}
            {tabValue === 1 && (
              <>
                <TextField label="Department Name" fullWidth value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
                <TextField label="Department Code" fullWidth value={formData.code || ''} onChange={(e) => setFormData({ ...formData, code: e.target.value })} />
                <TextField label="Dean / HOD" fullWidth value={formData.deanHod || ''} onChange={(e) => setFormData({ ...formData, deanHod: e.target.value })} />
                <TextField label="Email Address" fullWidth value={formData.email || ''} onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
                <TextField label="Phone Number" fullWidth value={formData.phone || ''} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} />
                <TextField label="Building Location" fullWidth value={formData.building || ''} onChange={(e) => setFormData({ ...formData, building: e.target.value })} />
              </>
            )}
            {tabValue === 2 && (
              <>
                <TextField label="Program Name" fullWidth value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
                <TextField label="Program Code" fullWidth value={formData.code || ''} onChange={(e) => setFormData({ ...formData, code: e.target.value })} />
                <TextField select label="Department" fullWidth value={formData.departmentId || ''} onChange={(e) => setFormData({ ...formData, departmentId: e.target.value })}>
                  {departments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
                </TextField>
              </>
            )}
            {tabValue === 3 && (
              <>
                <TextField label="Course Code" fullWidth value={formData.code || ''} onChange={(e) => setFormData({ ...formData, code: e.target.value })} />
                <TextField label="Course Name" fullWidth value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
                <TextField label="Credits" type="number" fullWidth value={formData.credits || ''} onChange={(e) => setFormData({ ...formData, credits: parseInt(e.target.value) })} />
                <TextField label="Duration" fullWidth value={formData.duration || ''} onChange={(e) => setFormData({ ...formData, duration: e.target.value })} />
                <TextField select label="Department" fullWidth value={formData.departmentId || ''} onChange={(e) => setFormData({ ...formData, departmentId: e.target.value })}>
                  {departments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
                </TextField>
                <TextField select label="Program" fullWidth value={formData.programId || ''} onChange={(e) => setFormData({ ...formData, programId: e.target.value })}>
                  {programs.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
                </TextField>
              </>
            )}
            {tabValue === 4 && (
              <>
                <TextField label="Semester Number" type="number" fullWidth value={formData.semesterNumber || ''} onChange={(e) => setFormData({ ...formData, semesterNumber: parseInt(e.target.value) })} />
                <TextField select label="Academic Year" fullWidth value={formData.academicYearId || ''} onChange={(e) => setFormData({ ...formData, academicYearId: e.target.value })}>
                  {academicYears.map((ay) => <MenuItem key={ay.id} value={ay.id}>{ay.name}</MenuItem>)}
                </TextField>
                <TextField select label="Program" fullWidth value={formData.programId || ''} onChange={(e) => setFormData({ ...formData, programId: e.target.value })}>
                  {programs.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
                </TextField>
                <TextField label="Start Date" type="date" InputLabelProps={{ shrink: true }} fullWidth value={formData.startDate?.split('T')[0] || ''} onChange={(e) => setFormData({ ...formData, startDate: e.target.value })} />
                <TextField label="End Date" type="date" InputLabelProps={{ shrink: true }} fullWidth value={formData.endDate?.split('T')[0] || ''} onChange={(e) => setFormData({ ...formData, endDate: e.target.value })} />
                <FormControlLabel control={<Checkbox checked={!!formData.currentSemester} onChange={(e) => setFormData({ ...formData, currentSemester: e.target.checked })} />} label="Current Semester" />
              </>
            )}
            {tabValue === 5 && (
              <>
                <TextField label="Subject Code" fullWidth value={formData.code || ''} onChange={(e) => setFormData({ ...formData, code: e.target.value })} />
                <TextField label="Subject Name" fullWidth value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
                <TextField label="Credits" type="number" fullWidth value={formData.credits || ''} onChange={(e) => setFormData({ ...formData, credits: parseInt(e.target.value) })} />
                <TextField select label="Department" fullWidth value={formData.departmentId || ''} onChange={(e) => setFormData({ ...formData, departmentId: e.target.value })}>
                  {departments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
                </TextField>
                <TextField select label="Semester" fullWidth value={formData.semesterId || ''} onChange={(e) => setFormData({ ...formData, semesterId: e.target.value })}>
                  {semesters.map((s) => <MenuItem key={s.id} value={s.id}>Sem {s.semesterNumber} ({s.programName})</MenuItem>)}
                </TextField>
                <TextField select label="Course Link" fullWidth value={formData.courseId || ''} onChange={(e) => setFormData({ ...formData, courseId: e.target.value })}>
                  {courses.map((c) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
                </TextField>
              </>
            )}
            {tabValue === 6 && (
              <>
                <TextField label="Section Name" fullWidth value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
                <TextField label="Capacity" type="number" fullWidth value={formData.capacity || ''} onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) })} />
                <TextField select label="Semester" fullWidth value={formData.semesterId || ''} onChange={(e) => setFormData({ ...formData, semesterId: e.target.value })}>
                  {semesters.map((s) => <MenuItem key={s.id} value={s.id}>Sem {s.semesterNumber} ({s.programName})</MenuItem>)}
                </TextField>
                <TextField select label="Department" fullWidth value={formData.departmentId || ''} onChange={(e) => setFormData({ ...formData, departmentId: e.target.value })}>
                  {departments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
                </TextField>
                <TextField select label="Program" fullWidth value={formData.programId || ''} onChange={(e) => setFormData({ ...formData, programId: e.target.value })}>
                  {programs.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
                </TextField>
                <TextField select label="Faculty Advisor" fullWidth value={formData.facultyAdvisorId || ''} onChange={(e) => setFormData({ ...formData, facultyAdvisorId: e.target.value })}>
                  {teachers.map((t) => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)}
                </TextField>
                <TextField select label="Academic Year" fullWidth value={formData.academicYearId || ''} onChange={(e) => setFormData({ ...formData, academicYearId: e.target.value })}>
                  {academicYears.map((ay) => <MenuItem key={ay.id} value={ay.id}>{ay.name}</MenuItem>)}
                </TextField>
              </>
            )}
            {tabValue === 7 && (
              <>
                <TextField label="Building Name" fullWidth value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
                <TextField label="Building Code" fullWidth value={formData.code || ''} onChange={(e) => setFormData({ ...formData, code: e.target.value })} />
                <TextField label="Floors" type="number" fullWidth value={formData.floors || ''} onChange={(e) => setFormData({ ...formData, floors: parseInt(e.target.value) })} />
              </>
            )}
            {tabValue === 8 && (
              <>
                <TextField label="Room Number" fullWidth value={formData.roomNumber || ''} onChange={(e) => setFormData({ ...formData, roomNumber: e.target.value })} />
                <TextField select label="Room Type" fullWidth value={formData.roomType || 'CLASSROOM'} onChange={(e) => setFormData({ ...formData, roomType: e.target.value })}>
                  <MenuItem value="CLASSROOM">CLASSROOM</MenuItem>
                  <MenuItem value="SEMINAR_HALL">SEMINAR HALL</MenuItem>
                  <MenuItem value="AUDITORIUM">AUDITORIUM</MenuItem>
                  <MenuItem value="LAB">LABORATORY</MenuItem>
                </TextField>
                <TextField label="Capacity" type="number" fullWidth value={formData.capacity || ''} onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) })} />
                <TextField select label="Building" fullWidth value={formData.buildingId || ''} onChange={(e) => setFormData({ ...formData, buildingId: e.target.value })}>
                  {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
                </TextField>
                <TextField label="Floor" type="number" fullWidth value={formData.floor || ''} onChange={(e) => setFormData({ ...formData, floor: parseInt(e.target.value) })} />
                <FormControlLabel control={<Checkbox checked={!!formData.projector} onChange={(e) => setFormData({ ...formData, projector: e.target.checked })} />} label="Has Projector" />
                <FormControlLabel control={<Checkbox checked={!!formData.smartBoard} onChange={(e) => setFormData({ ...formData, smartBoard: e.target.checked })} />} label="Has Smart Board" />
                <FormControlLabel control={<Checkbox checked={!!formData.airConditioning} onChange={(e) => setFormData({ ...formData, airConditioning: e.target.checked })} />} label="Has Air Conditioning" />
              </>
            )}
            {tabValue === 9 && (
              <>
                <TextField label="Lab Name" fullWidth value={formData.labName || ''} onChange={(e) => setFormData({ ...formData, labName: e.target.value })} />
                <TextField select label="Department" fullWidth value={formData.departmentId || ''} onChange={(e) => setFormData({ ...formData, departmentId: e.target.value })}>
                  {departments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
                </TextField>
                <TextField label="Student Capacity" type="number" fullWidth value={formData.capacity || ''} onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) })} />
                <TextField label="Total Systems" type="number" fullWidth value={formData.systems || ''} onChange={(e) => setFormData({ ...formData, systems: parseInt(e.target.value) })} />
                <TextField label="Lab Assistant Name" fullWidth value={formData.labAssistant || ''} onChange={(e) => setFormData({ ...formData, labAssistant: e.target.value })} />
              </>
            )}
            {tabValue === 10 && (
              <>
                <TextField select label="Department" fullWidth value={formData.departmentId || ''} onChange={(e) => setFormData({ ...formData, departmentId: e.target.value })}>
                  {departments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
                </TextField>
                <TextField select label="Subject Link" fullWidth value={formData.subjectId || ''} onChange={(e) => setFormData({ ...formData, subjectId: e.target.value })}>
                  {subjects.map((s) => <MenuItem key={s.id} value={s.id}>{s.name} ({s.code})</MenuItem>)}
                </TextField>
                <TextField select label="Faculty Member" fullWidth value={formData.facultyId || ''} onChange={(e) => setFormData({ ...formData, facultyId: e.target.value })}>
                  {teachers.map((t) => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)}
                </TextField>
                <TextField select label="Section Link" fullWidth value={formData.sectionId || ''} onChange={(e) => setFormData({ ...formData, sectionId: e.target.value })}>
                  {sections.map((sec) => <MenuItem key={sec.id} value={sec.id}>{sec.name}</MenuItem>)}
                </TextField>
                <TextField select label="Semester Link" fullWidth value={formData.semesterId || ''} onChange={(e) => setFormData({ ...formData, semesterId: e.target.value })}>
                  {semesters.map((s) => <MenuItem key={s.id} value={s.id}>Sem {s.semesterNumber} ({s.programName})</MenuItem>)}
                </TextField>
                <TextField select label="Academic Year Link" fullWidth value={formData.academicYearId || ''} onChange={(e) => setFormData({ ...formData, academicYearId: e.target.value })}>
                  {academicYears.map((ay) => <MenuItem key={ay.id} value={ay.id}>{ay.name}</MenuItem>)}
                </TextField>
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AcademicDashboard;
