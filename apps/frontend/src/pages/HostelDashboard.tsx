import React, { useState } from 'react';
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
  Checkbox,
  FormControlLabel
} from '@mui/material';
import {
  Home as HostelIcon,
  Description as AppIcon,
  Hotel as BedIcon,
  People as VisitorIcon,
  ReportProblem as ComplaintIcon,
  Restaurant as MessIcon,
  TrendingUp as AnalyticsIcon,
  MoneyOff as WaiverIcon
} from '@mui/icons-material';

export const HostelDashboard: React.FC = () => {
  const [tab, setTab] = useState<string>('STRUCTURE');

  // --- STATE ---
  const [hostels, setHostels] = useState<any[]>([
    { id: 'h-1', name: 'Boys Hostel Wing A', code: 'BH-A', hostelType: 'BOYS', capacity: 150, contactPhone: '9988776655', active: true },
    { id: 'h-2', name: 'Girls Hostel Wing B', code: 'GH-B', hostelType: 'GIRLS', capacity: 120, contactPhone: '9988776644', active: true }
  ]);

  const [blocks] = useState<any[]>([
    { id: 'b-1', hostelId: 'h-1', name: 'Alpha Block', code: 'ALPH-01', totalFloors: 3, active: true },
    { id: 'b-2', hostelId: 'h-2', name: 'Omega Block', code: 'OMEG-02', totalFloors: 2, active: true }
  ]);

  const [rooms] = useState<any[]>([
    { id: 'r-1', roomNumber: 'A-101', roomType: 'DOUBLE', capacity: 2, monthlyRate: 3500.00, status: 'AVAILABLE', active: true },
    { id: 'r-2', roomNumber: 'A-102', roomType: 'SINGLE', capacity: 1, monthlyRate: 6000.00, status: 'FULL', active: true },
    { id: 'r-3', roomNumber: 'B-201', roomType: 'TRIPLE', capacity: 3, monthlyRate: 3000.00, status: 'PARTIALLY_OCCUPIED', active: true }
  ]);

  const [beds, setBeds] = useState<any[]>([
    { id: 'bed-1', roomNumber: 'A-101', bedNumber: 'A-101-B1', status: 'AVAILABLE' },
    { id: 'bed-2', roomNumber: 'A-101', bedNumber: 'A-101-B2', status: 'AVAILABLE' },
    { id: 'bed-3', roomNumber: 'A-102', bedNumber: 'A-102-B1', status: 'ALLOCATED' }
  ]);

  const [applications, setApplications] = useState<any[]>([
    { id: 'app-1', studentName: 'Samantha Vance', preferredHostelName: 'Girls Hostel Wing B', preferredRoomType: 'SINGLE', status: 'SUBMITTED', submittedAt: '2026-07-05' },
    { id: 'app-2', studentName: 'Marcus Vance', preferredHostelName: 'Boys Hostel Wing A', preferredRoomType: 'DOUBLE', status: 'APPROVED', submittedAt: '2026-07-06' }
  ]);

  const [allocations, setAllocations] = useState<any[]>([
    { id: 'al-1', studentName: 'Demo Student', bedNumber: 'A-102-B1', status: 'ACTIVE', startDate: '2026-07-01' }
  ]);

  const [visitors, setVisitors] = useState<any[]>([
    { id: 'vis-1', visitorName: 'John Doe Sr', relation: 'Father', phone: '555-0199', purpose: 'Monthly Visit', identityReferenceMasked: 'XXX-XX-5678', status: 'CHECKED_IN' }
  ]);

  const [complaints, setComplaints] = useState<any[]>([
    { id: 'comp-1', studentName: 'Marcus Vance', category: 'ELECTRICAL', priority: 'HIGH', description: 'Light fixture flickers in room A-101', status: 'OPEN' }
  ]);

  const [messPlans] = useState<any[]>([
    { id: 'mp-1', name: 'Standard Vegetarian', costPerMonth: 2200.00, foodType: 'VEG' },
    { id: 'mp-2', name: 'Mixed Premium', costPerMonth: 3000.00, foodType: 'MIXED' }
  ]);

  const [fines, setFines] = useState<any[]>([
    { id: 'fine-1', studentName: 'Demo Student', amount: 150.00, reason: 'Broken Chair', status: 'PENDING' }
  ]);

  // Dialog States
  const [openHostelDlg, setOpenHostelDlg] = useState(false);
  const [openAllocDlg, setOpenAllocDlg] = useState(false);
  const [openCheckInDlg, setOpenCheckInDlg] = useState(false);
  const [openCheckOutDlg, setOpenCheckOutDlg] = useState(false);
  const [openVisitorDlg, setOpenVisitorDlg] = useState(false);
  const [openComplaintDlg, setOpenComplaintDlg] = useState(false);
  const [openWaiverDlg, setOpenWaiverDlg] = useState(false);

  // Form Field States
  const [newHostel, setNewHostel] = useState({ name: '', code: '', hostelType: 'BOYS', capacity: 100 });
  const [newAlloc, setNewAlloc] = useState({ applicationId: '', bedId: '' });
  const [checkInFields, setCheckInFields] = useState({ inventoryNotes: '', conditionNotes: '', acknowledgement: false });
  const [checkOutFields, setCheckOutFields] = useState({ damageCost: 0.0, damageNotes: '' });
  const [newVisitor, setNewVisitor] = useState({ visitorName: '', phone: '', relation: '', purpose: '', identityReference: '' });
  const [newComplaint, setNewComplaint] = useState({ category: 'ELECTRICAL', priority: 'MEDIUM', description: '' });
  const [waiverReason, setWaiverReason] = useState('');
  const [selectedFineId, setSelectedFineId] = useState('');
  const [selectedAllocationId, setSelectedAllocationId] = useState('');

  const handleAddHostel = () => {
    if (!newHostel.name || !newHostel.code) return;
    setHostels([...hostels, {
      id: `h-${Date.now()}`,
      ...newHostel,
      active: true
    }]);
    setOpenHostelDlg(false);
    setNewHostel({ name: '', code: '', hostelType: 'BOYS', capacity: 100 });
  };

  const handleReviewApp = (id: string, newStatus: string) => {
    setApplications(applications.map(a => a.id === id ? { ...a, status: newStatus } : a));
  };

  const handleAddAllocation = () => {
    if (!newAlloc.applicationId || !newAlloc.bedId) return;
    const appRecord = applications.find(a => a.id === newAlloc.applicationId);
    const targetBed = beds.find(b => b.id === newAlloc.bedId);
    if (!appRecord || !targetBed) return;

    setAllocations([...allocations, {
      id: `al-${Date.now()}`,
      studentName: appRecord.studentName,
      bedNumber: targetBed.bedNumber,
      status: 'ACTIVE',
      startDate: new Date().toISOString().split('T')[0]
    }]);

    setBeds(beds.map(b => b.id === targetBed.id ? { ...b, status: 'ALLOCATED' } : b));
    setApplications(applications.map(a => a.id === appRecord.id ? { ...a, status: 'ALLOCATED' } : a));
    setOpenAllocDlg(false);
  };

  const handleCheckIn = () => {
    setOpenCheckInDlg(false);
  };

  const handleCheckOut = () => {
    const allocRecord = allocations.find(al => al.id === selectedAllocationId);
    if (!allocRecord) return;

    // Release Bed
    setBeds(beds.map(b => b.bedNumber === allocRecord.bedNumber ? { ...b, status: 'AVAILABLE' } : b));
    setAllocations(allocations.map(al => al.id === selectedAllocationId ? { ...al, status: 'COMPLETED' } : al));

    if (checkOutFields.damageCost > 0) {
      setFines([...fines, {
        id: `fine-${Date.now()}`,
        studentName: allocRecord.studentName,
        amount: checkOutFields.damageCost,
        reason: checkOutFields.damageNotes || 'Checkout damage assessment fee',
        status: 'PENDING'
      }]);
    }

    setOpenCheckOutDlg(false);
  };

  const handleAddVisitor = () => {
    if (!newVisitor.visitorName || !newVisitor.phone) return;
    setVisitors([...visitors, {
      id: `vis-${Date.now()}`,
      ...newVisitor,
      identityReferenceMasked: `XXX-XX-${newVisitor.identityReference.slice(-4) || '1234'}`,
      status: 'CHECKED_IN'
    }]);
    setOpenVisitorDlg(false);
    setNewVisitor({ visitorName: '', phone: '', relation: '', purpose: '', identityReference: '' });
  };

  const handleVisitorCheckOut = (id: string) => {
    setVisitors(visitors.map(v => v.id === id ? { ...v, status: 'CHECKED_OUT' } : v));
  };

  const handleAddComplaint = () => {
    if (!newComplaint.description) return;
    setComplaints([...complaints, {
      id: `comp-${Date.now()}`,
      studentName: 'Samantha Vance',
      ...newComplaint,
      status: 'OPEN'
    }]);
    setOpenComplaintDlg(false);
    setNewComplaint({ category: 'ELECTRICAL', priority: 'MEDIUM', description: '' });
  };

  const handleResolveComplaint = (id: string) => {
    setComplaints(complaints.map(c => c.id === id ? { ...c, status: 'RESOLVED' } : c));
  };

  const handleWaiveFine = () => {
    if (!selectedFineId) return;
    setFines(fines.map(f => f.id === selectedFineId ? { ...f, status: 'WAIVED' } : f));
    setOpenWaiverDlg(false);
    setWaiverReason('');
  };

  return (
    <Box sx={{ p: 4, bgcolor: '#f4f6f8', minHeight: '100vh' }}>
      {/* Title */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight="bold" color="primary">
          Smart Hostel Portal
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Active Environment: SQLite Demo Mode
        </Typography>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 4, borderRadius: 2 }}>
        <Tabs
          value={tab}
          onChange={(_, newTab) => setTab(newTab)}
          indicatorColor="primary"
          textColor="primary"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<HostelIcon />} label="Structure Setup" value="STRUCTURE" />
          <Tab icon={<AppIcon />} label="Applications" value="APPLICATIONS" />
          <Tab icon={<BedIcon />} label="Allocations" value="ALLOCATIONS" />
          <Tab icon={<VisitorIcon />} label="Visitors Log" value="VISITORS" />
          <Tab icon={<ComplaintIcon />} label="Complaints" value="COMPLAINTS" />
          <Tab icon={<MessIcon />} label="Mess Planner" value="MESS" />
          <Tab icon={<WaiverIcon />} label="Fines Ledger" value="FINES" />
          <Tab icon={<AnalyticsIcon />} label="Occupancy Stats" value="ANALYTICS" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      {tab === 'STRUCTURE' && (
        <Box>
          <Grid container spacing={3}>
            {/* Hostels Table */}
            <Grid item xs={12}>
              <Paper sx={{ p: 3, borderRadius: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" fontWeight="bold">Hostels Registry</Typography>
                  <Button variant="contained" size="small" onClick={() => setOpenHostelDlg(true)}>Add Hostel</Button>
                </Box>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Hostel Name</TableCell>
                        <TableCell>Code</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Capacity</TableCell>
                        <TableCell>Phone</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {hostels.map(h => (
                        <TableRow key={h.id}>
                          <TableCell>{h.name}</TableCell>
                          <TableCell>{h.code}</TableCell>
                          <TableCell><Chip label={h.hostelType} size="small" /></TableCell>
                          <TableCell>{h.capacity} beds</TableCell>
                          <TableCell>{h.contactPhone || 'N/A'}</TableCell>
                          <TableCell>
                            <Chip label={h.active ? 'Active' : 'Inactive'} color={h.active ? 'success' : 'default'} size="small" />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>

            {/* Blocks & Rooms Grid */}
            <Grid item xs={6}>
              <Paper sx={{ p: 3, borderRadius: 2 }}>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Hostel Blocks</Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Block Code</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Floors</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {blocks.map(b => (
                        <TableRow key={b.id}>
                          <TableCell>{b.code}</TableCell>
                          <TableCell>{b.name}</TableCell>
                          <TableCell>{b.totalFloors} floors</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>

            <Grid item xs={6}>
              <Paper sx={{ p: 3, borderRadius: 2 }}>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Rooms Details</Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Room No</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Rate</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {rooms.map(r => (
                        <TableRow key={r.id}>
                          <TableCell>{r.roomNumber}</TableCell>
                          <TableCell>{r.roomType}</TableCell>
                          <TableCell>₹{r.monthlyRate}/mo</TableCell>
                          <TableCell>
                            <Chip
                              label={r.status}
                              color={r.status === 'AVAILABLE' ? 'success' : r.status === 'FULL' ? 'error' : 'warning'}
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}

      {tab === 'APPLICATIONS' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Student Applications</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student Name</TableCell>
                  <TableCell>Preferred Hostel</TableCell>
                  <TableCell>Room Type Preference</TableCell>
                  <TableCell>Submitted Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {applications.map(a => (
                  <TableRow key={a.id}>
                    <TableCell>{a.studentName}</TableCell>
                    <TableCell>{a.preferredHostelName}</TableCell>
                    <TableCell>{a.preferredRoomType}</TableCell>
                    <TableCell>{a.submittedAt}</TableCell>
                    <TableCell>
                      <Chip
                        label={a.status}
                        color={a.status === 'APPROVED' ? 'success' : a.status === 'REJECTED' ? 'error' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {a.status === 'SUBMITTED' && (
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button variant="contained" color="success" size="small" onClick={() => handleReviewApp(a.id, 'APPROVED')}>Approve</Button>
                          <Button variant="outlined" color="error" size="small" onClick={() => handleReviewApp(a.id, 'REJECTED')}>Reject</Button>
                        </Box>
                      )}
                      {a.status === 'APPROVED' && (
                        <Button variant="contained" size="small" color="secondary" onClick={() => {
                          setNewAlloc({ ...newAlloc, applicationId: a.id });
                          setOpenAllocDlg(true);
                        }}>Allocate Bed</Button>
                      )}
                      {a.status === 'ALLOCATED' && (
                        <Typography variant="body2" color="textSecondary">Allocated</Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tab === 'ALLOCATIONS' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Active Bed Allocations</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student Name</TableCell>
                  <TableCell>Bed Number</TableCell>
                  <TableCell>Allocation Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {allocations.map(al => (
                  <TableRow key={al.id}>
                    <TableCell>{al.studentName}</TableCell>
                    <TableCell>{al.bedNumber}</TableCell>
                    <TableCell>{al.startDate}</TableCell>
                    <TableCell>
                      <Chip label={al.status} color={al.status === 'ACTIVE' ? 'success' : 'default'} size="small" />
                    </TableCell>
                    <TableCell>
                      {al.status === 'ACTIVE' && (
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button variant="contained" size="small" onClick={() => setOpenCheckInDlg(true)}>Check-In</Button>
                          <Button variant="outlined" color="error" size="small" onClick={() => {
                            setSelectedAllocationId(al.id);
                            setOpenCheckOutDlg(true);
                          }}>Check-Out</Button>
                        </Box>
                      )}
                    </TableCell>
                  </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tab === 'VISITORS' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" fontWeight="bold">Hostel Visitors Registry</Typography>
            <Button variant="contained" onClick={() => setOpenVisitorDlg(true)}>Log Visitor Check-In</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Visitor Name</TableCell>
                  <TableCell>Relation</TableCell>
                  <TableCell>Phone</TableCell>
                  <TableCell>Purpose</TableCell>
                  <TableCell>ID Masked Reference</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {visitors.map(v => (
                  <TableRow key={v.id}>
                    <TableCell>{v.visitorName}</TableCell>
                    <TableCell>{v.relation}</TableCell>
                    <TableCell>{v.phone}</TableCell>
                    <TableCell>{v.purpose}</TableCell>
                    <TableCell><code>{v.identityReferenceMasked}</code></TableCell>
                    <TableCell>
                      <Chip label={v.status} color={v.status === 'CHECKED_IN' ? 'primary' : 'default'} size="small" />
                    </TableCell>
                    <TableCell>
                      {v.status === 'CHECKED_IN' && (
                        <Button variant="outlined" color="warning" size="small" onClick={() => handleVisitorCheckOut(v.id)}>Log Checkout</Button>
                      )}
                    </TableCell>
                  </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tab === 'COMPLAINTS' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" fontWeight="bold">Maintenance & Complaints</Typography>
            <Button variant="contained" onClick={() => setOpenComplaintDlg(true)}>Log Complaint</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Logged By</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {complaints.map(c => (
                  <TableRow key={c.id}>
                    <TableCell>{c.studentName}</TableCell>
                    <TableCell><Chip label={c.category} size="small" /></TableCell>
                    <TableCell>
                      <Chip label={c.priority} color={c.priority === 'CRITICAL' || c.priority === 'HIGH' ? 'error' : 'default'} size="small" />
                    </TableCell>
                    <TableCell>{c.description}</TableCell>
                    <TableCell>
                      <Chip label={c.status} color={c.status === 'RESOLVED' ? 'success' : 'warning'} size="small" />
                    </TableCell>
                    <TableCell>
                      {c.status === 'OPEN' && (
                        <Button variant="contained" color="success" size="small" onClick={() => handleResolveComplaint(c.id)}>Mark Resolved</Button>
                      )}
                    </TableCell>
                  </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tab === 'MESS' && (
        <Grid container spacing={3}>
          <Grid item xs={6}>
            <Paper sx={{ p: 3, borderRadius: 2 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Mess Subscription Plans</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Plan Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Cost/Month</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {messPlans.map(mp => (
                      <TableRow key={mp.id}>
                        <TableCell>{mp.name}</TableCell>
                        <TableCell><Chip label={mp.foodType} size="small" /></TableCell>
                        <TableCell>₹{mp.costPerMonth}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          <Grid item xs={6}>
            <Paper sx={{ p: 3, borderRadius: 2 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Weekly Meal Menu</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Day</TableCell>
                      <TableCell>Breakfast</TableCell>
                      <TableCell>Lunch</TableCell>
                      <TableCell>Dinner</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>Monday</TableCell>
                      <TableCell>Idli Sambhar</TableCell>
                      <TableCell>Rice, Dal, Veg Curry</TableCell>
                      <TableCell>Roti, Paneer Masala</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Tuesday</TableCell>
                      <TableCell>Poha, Tea</TableCell>
                      <TableCell>Rice, Sambhar, Papad</TableCell>
                      <TableCell>Mix Veg, Paratha</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>
      )}

      {tab === 'FINES' && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Hostel Fines Ledger</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Student Name</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {fines.map(f => (
                  <TableRow key={f.id}>
                    <TableCell>{f.studentName}</TableCell>
                    <TableCell>₹{f.amount}</TableCell>
                    <TableCell>{f.reason}</TableCell>
                    <TableCell>
                      <Chip label={f.status} color={f.status === 'WAIVED' ? 'success' : 'error'} size="small" />
                    </TableCell>
                    <TableCell>
                      {f.status === 'PENDING' && (
                        <Button variant="contained" color="warning" size="small" onClick={() => {
                          setSelectedFineId(f.id);
                          setOpenWaiverDlg(true);
                        }}>Waive Fine</Button>
                      )}
                    </TableCell>
                  </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tab === 'ANALYTICS' && (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={3}>
              <Card sx={{ borderRadius: 2 }}>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>Total Hostels</Typography>
                  <Typography variant="h4" fontWeight="bold">2</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={3}>
              <Card sx={{ borderRadius: 2 }}>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>Active Allocations</Typography>
                  <Typography variant="h4" fontWeight="bold">1</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={3}>
              <Card sx={{ borderRadius: 2 }}>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>Occupancy Percentage</Typography>
                  <Typography variant="h4" fontWeight="bold">33.3%</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={3}>
              <Card sx={{ borderRadius: 2 }}>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>Pending Applications</Typography>
                  <Typography variant="h4" fontWeight="bold">1</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* --- DIALOGS --- */}

      {/* Add Hostel Dialog */}
      <Dialog open={openHostelDlg} onClose={() => setOpenHostelDlg(false)}>
        <DialogTitle>Add New Hostel</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField label="Hostel Name" fullWidth value={newHostel.name} onChange={e => setNewHostel({ ...newHostel, name: e.target.value })} />
          <TextField label="Hostel Code" fullWidth value={newHostel.code} onChange={e => setNewHostel({ ...newHostel, code: e.target.value })} />
          <FormControl fullWidth>
            <InputLabel>Hostel Type</InputLabel>
            <Select value={newHostel.hostelType} label="Hostel Type" onChange={e => setNewHostel({ ...newHostel, hostelType: e.target.value as string })}>
              <MenuItem value="BOYS">BOYS</MenuItem>
              <MenuItem value="GIRLS">GIRLS</MenuItem>
              <MenuItem value="COED">COED</MenuItem>
            </Select>
          </FormControl>
          <TextField label="Capacity" type="number" fullWidth value={newHostel.capacity} onChange={e => setNewHostel({ ...newHostel, capacity: parseInt(e.target.value) })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenHostelDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddHostel}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Allocate Bed Dialog */}
      <Dialog open={openAllocDlg} onClose={() => setOpenAllocDlg(false)}>
        <DialogTitle>Allocate Bed to Student</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <FormControl fullWidth>
            <InputLabel>Select Bed</InputLabel>
            <Select value={newAlloc.bedId} label="Select Bed" onChange={e => setNewAlloc({ ...newAlloc, bedId: e.target.value as string })}>
              {beds.filter(b => b.status === 'AVAILABLE').map(b => (
                <MenuItem key={b.id} value={b.id}>{b.bedNumber}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAllocDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddAllocation}>Allocate</Button>
        </DialogActions>
      </Dialog>

      {/* Check In Dialog */}
      <Dialog open={openCheckInDlg} onClose={() => setOpenCheckInDlg(false)}>
        <DialogTitle>Student Check-In Handover Checklist</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField label="Inventory Handover Notes" fullWidth value={checkInFields.inventoryNotes} onChange={e => setCheckInFields({ ...checkInFields, inventoryNotes: e.target.value })} />
          <TextField label="Room Condition Notes" fullWidth value={checkInFields.conditionNotes} onChange={e => setCheckInFields({ ...checkInFields, conditionNotes: e.target.value })} />
          <FormControlLabel
            control={<Checkbox checked={checkInFields.acknowledgement} onChange={e => setCheckInFields({ ...checkInFields, acknowledgement: e.target.checked })} />}
            label="I verify student identity and room inventory handover"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCheckInDlg(false)}>Cancel</Button>
          <Button variant="contained" disabled={!checkInFields.acknowledgement} onClick={handleCheckIn}>Complete Check-In</Button>
        </DialogActions>
      </Dialog>

      {/* Check Out Dialog */}
      <Dialog open={openCheckOutDlg} onClose={() => setOpenCheckOutDlg(false)}>
        <DialogTitle>Bed Checkout Damage Assessment</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField label="Assessed Damage Fine Cost (INR)" type="number" fullWidth value={checkOutFields.damageCost} onChange={e => setCheckOutFields({ ...checkOutFields, damageCost: parseFloat(e.target.value) })} />
          <TextField label="Damage & Inventory Issues Notes" fullWidth value={checkOutFields.damageNotes} onChange={e => setCheckOutFields({ ...checkOutFields, damageNotes: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCheckOutDlg(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleCheckOut}>Complete Check-Out & Release</Button>
        </DialogActions>
      </Dialog>

      {/* Visitor Dialog */}
      <Dialog open={openVisitorDlg} onClose={() => setOpenVisitorDlg(false)}>
        <DialogTitle>Log Visitor Logbook Entry</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField label="Visitor Name" fullWidth value={newVisitor.visitorName} onChange={e => setNewVisitor({ ...newVisitor, visitorName: e.target.value })} />
          <TextField label="Visitor Phone" fullWidth value={newVisitor.phone} onChange={e => setNewVisitor({ ...newVisitor, phone: e.target.value })} />
          <TextField label="Relation" fullWidth value={newVisitor.relation} onChange={e => setNewVisitor({ ...newVisitor, relation: e.target.value })} />
          <TextField label="Purpose of Visit" fullWidth value={newVisitor.purpose} onChange={e => setNewVisitor({ ...newVisitor, purpose: e.target.value })} />
          <TextField label="Identity Document Reference" fullWidth value={newVisitor.identityReference} onChange={e => setNewVisitor({ ...newVisitor, identityReference: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenVisitorDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddVisitor}>Log Check-In</Button>
        </DialogActions>
      </Dialog>

      {/* Complaint Dialog */}
      <Dialog open={openComplaintDlg} onClose={() => setOpenComplaintDlg(false)}>
        <DialogTitle>File Maintenance Complaint</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <FormControl fullWidth>
            <InputLabel>Category</InputLabel>
            <Select value={newComplaint.category} label="Category" onChange={e => setNewComplaint({ ...newComplaint, category: e.target.value as string })}>
              <MenuItem value="ELECTRICAL">ELECTRICAL</MenuItem>
              <MenuItem value="PLUMBING">PLUMBING</MenuItem>
              <MenuItem value="CLEANING">CLEANING</MenuItem>
              <MenuItem value="INTERNET">INTERNET</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Priority</InputLabel>
            <Select value={newComplaint.priority} label="Priority" onChange={e => setNewComplaint({ ...newComplaint, priority: e.target.value as string })}>
              <MenuItem value="LOW">LOW</MenuItem>
              <MenuItem value="MEDIUM">MEDIUM</MenuItem>
              <MenuItem value="HIGH">HIGH</MenuItem>
              <MenuItem value="CRITICAL">CRITICAL</MenuItem>
            </Select>
          </FormControl>
          <TextField label="Issue Description" multiline rows={3} fullWidth value={newComplaint.description} onChange={e => setNewComplaint({ ...newComplaint, description: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenComplaintDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddComplaint}>Submit Issue</Button>
        </DialogActions>
      </Dialog>

      {/* Waive Fine Dialog */}
      <Dialog open={openWaiverDlg} onClose={() => setOpenWaiverDlg(false)}>
        <DialogTitle>Waive Student Penalty Dues</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField label="Official Waiver Reason" multiline rows={2} fullWidth value={waiverReason} onChange={e => setWaiverReason(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenWaiverDlg(false)}>Cancel</Button>
          <Button variant="contained" color="warning" disabled={!waiverReason} onClick={handleWaiveFine}>Confirm Waiver</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
export default HostelDashboard;
