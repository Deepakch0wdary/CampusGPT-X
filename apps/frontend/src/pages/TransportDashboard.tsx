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
  Divider
} from '@mui/material';
import {
  DirectionsBus as TransportIcon,
  Timeline as RouteIcon,
  Place as StopIcon,
  Description as AppIcon,
  CardMembership as SubscriptionIcon,
  Map as LiveMapIcon,
  Build as MaintenanceIcon,
  LocalGasStation as FuelIcon,
  ReportProblem as IncidentIcon,
  BarChart as AnalyticsIcon
} from '@mui/icons-material';

export const TransportDashboard: React.FC = () => {
  const [tab, setTab] = useState<string>('DASHBOARD');

  // --- STATE MOCKS & HANDLERS ---
  const [vehicles, setVehicles] = useState<any[]>([
    { id: 'v-1', registrationNumber: 'KA-01-F-1234', vehicleCode: 'BUS-01', vehicleType: 'ELECTRIC_BUS', manufacturer: 'Tata', model: 'Ultra', seatingCapacity: 40, status: 'ACTIVE', gpsDeviceId: 'GPS-9922' },
    { id: 'v-2', registrationNumber: 'KA-03-M-5678', vehicleCode: 'VAN-02', vehicleType: 'VAN', manufacturer: 'Force', model: 'Traveler', seatingCapacity: 15, status: 'MAINTENANCE', gpsDeviceId: 'GPS-4411' }
  ]);

  const [routes, setRoutes] = useState<any[]>([
    { id: 'r-1', name: 'Campus Main Loop', code: 'RT-01', origin: 'City Terminal', destination: 'Main Campus', estimatedDistanceKm: 12.5, estimatedDurationMinutes: 30, status: 'ACTIVE' },
    { id: 'r-2', name: 'Metro Connector Route', code: 'RT-02', origin: 'Metro Junction', destination: 'University Gate', estimatedDistanceKm: 6.2, estimatedDurationMinutes: 15, status: 'ACTIVE' }
  ]);

  const [stops, setStops] = useState<any[]>([
    { id: 's-1', name: 'City Terminal', code: 'ST-01', address: 'Central bus depot', latitude: 12.9716, longitude: 77.5946 },
    { id: 's-2', name: 'Metro Junction', code: 'ST-02', address: 'Phase-2 Metro exit gate', latitude: 12.9279, longitude: 77.6271 },
    { id: 's-3', name: 'University Gate', code: 'ST-03', address: 'Arch road entry', latitude: 12.9104, longitude: 77.6409 },
    { id: 's-4', name: 'Main Campus', code: 'ST-04', address: 'Admin Block quad', latitude: 12.9080, longitude: 77.6450 }
  ]);

  const [applications, setApplications] = useState<any[]>([
    { id: 'app-1', applicantName: 'Samantha Student', routeCode: 'RT-01', pickupStop: 'Metro Junction', dropStop: 'Main Campus', status: 'SUBMITTED', submittedAt: '2026-07-06' },
    { id: 'app-2', applicantName: 'Marcus Teacher', routeCode: 'RT-02', pickupStop: 'University Gate', dropStop: 'Main Campus', status: 'APPROVED', submittedAt: '2026-07-07' }
  ]);

  const [subscriptions, setSubscriptions] = useState<any[]>([
    { id: 'sub-1', userName: 'Marcus Teacher', routeCode: 'RT-02', pickupStop: 'University Gate', status: 'ACTIVE', startDate: '2026-07-01', endDate: '2026-12-31' }
  ]);

  const [trips] = useState<any[]>([
    { id: 't-1', routeCode: 'RT-01', vehicleCode: 'BUS-01', status: 'IN_PROGRESS', delayMinutes: 5, scheduledStartAt: '08:00 AM', actualStartAt: '08:05 AM' }
  ]);

  const [maintenances] = useState<any[]>([
    { id: 'm-1', vehicleCode: 'BUS-01', maintenanceType: 'SERVICE', scheduledDate: '2026-07-10', estimatedCost: 4500.00, status: 'SCHEDULED' }
  ]);

  const [fuelLogs, setFuelLogs] = useState<any[]>([
    { id: 'f-1', vehicleCode: 'BUS-01', filledAt: '2026-07-06', quantityLitres: 45.5, totalAmount: 4322.50, odometerKm: 12040 }
  ]);

  const [incidents, setIncidents] = useState<any[]>([
    { id: 'i-1', vehicleCode: 'VAN-02', type: 'BREAKDOWN', severity: 'HIGH', description: 'Engine overheating on outer ring road', occurredAt: '2026-07-07', status: 'OPEN' }
  ]);

  // Dialog State
  const [openVehicleDlg, setOpenVehicleDlg] = useState(false);
  const [openRouteDlg, setOpenRouteDlg] = useState(false);
  const [openStopDlg, setOpenStopDlg] = useState(false);
  const [openAppDlg, setOpenAppDlg] = useState(false);
  const [openIncidentDlg, setOpenIncidentDlg] = useState(false);
  const [openFuelDlg, setOpenFuelDlg] = useState(false);

  // Form states
  const [newVehicle, setNewVehicle] = useState({ registrationNumber: '', vehicleCode: '', vehicleType: 'BUS', manufacturer: '', model: '', seatingCapacity: 40, gpsDeviceId: '' });
  const [newRoute, setNewRoute] = useState({ name: '', code: '', origin: '', destination: '', estimatedDistanceKm: 10, estimatedDurationMinutes: 20 });
  const [newStop, setNewStop] = useState({ name: '', code: '', address: '', latitude: 12.9, longitude: 77.6 });
  const [newApp, setNewApp] = useState({ routeId: '', pickupStopId: '', dropStopId: '' });
  const [newIncident, setNewIncident] = useState({ vehicleId: '', type: 'BREAKDOWN', severity: 'MEDIUM', description: '', locationText: '' });
  const [newFuel, setNewFuel] = useState({ vehicleId: '', quantityLitres: 50.0, totalAmount: 4800.00, odometerKm: 10000, fuelStation: 'Bharat Petroleum' });

  const handleAddVehicle = () => {
    if (!newVehicle.registrationNumber || !newVehicle.vehicleCode) return;
    setVehicles([...vehicles, {
      id: `v-${Date.now()}`,
      ...newVehicle,
      status: 'ACTIVE'
    }]);
    setOpenVehicleDlg(false);
  };

  const handleAddRoute = () => {
    if (!newRoute.name || !newRoute.code) return;
    setRoutes([...routes, {
      id: `r-${Date.now()}`,
      ...newRoute,
      status: 'ACTIVE'
    }]);
    setOpenRouteDlg(false);
  };

  const handleAddStop = () => {
    if (!newStop.name || !newStop.code) return;
    setStops([...stops, {
      id: `s-${Date.now()}`,
      ...newStop
    }]);
    setOpenStopDlg(false);
  };

  const handleAddIncident = () => {
    if (!newIncident.description) return;
    const targetVeh = vehicles.find(v => v.id === newIncident.vehicleId);
    setIncidents([...incidents, {
      id: `i-${Date.now()}`,
      vehicleCode: targetVeh?.vehicleCode || 'BUS-01',
      ...newIncident,
      occurredAt: new Date().toISOString().split('T')[0],
      status: 'OPEN'
    }]);
    setOpenIncidentDlg(false);
  };

  const handleAddFuel = () => {
    const targetVeh = vehicles.find(v => v.id === newFuel.vehicleId);
    setFuelLogs([...fuelLogs, {
      id: `f-${Date.now()}`,
      vehicleCode: targetVeh?.vehicleCode || 'BUS-01',
      filledAt: new Date().toISOString().split('T')[0],
      ...newFuel
    }]);
    setOpenFuelDlg(false);
  };

  const handleReviewApp = (id: string, decision: string) => {
    setApplications(applications.map(a => a.id === id ? { ...a, status: decision } : a));
    if (decision === 'APPROVED') {
      const app = applications.find(a => a.id === id);
      setSubscriptions([...subscriptions, {
        id: `sub-${Date.now()}`,
        userName: app?.applicantName || 'Samantha Student',
        routeCode: app?.routeCode || 'RT-01',
        pickupStop: app?.pickupStop || 'Metro Junction',
        status: 'ACTIVE',
        startDate: new Date().toISOString().split('T')[0],
        endDate: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      }]);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          Smart Transport Portal
        </Typography>
        <Chip label="Transport Network Online" color="success" size="small" />
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tab}
          onChange={(_, val) => setTab(val)}
          variant="scrollable"
          scrollButtons="auto"
          textColor="primary"
          indicatorColor="primary"
        >
          <Tab icon={<AnalyticsIcon />} label="Dashboard" value="DASHBOARD" />
          <Tab icon={<TransportIcon />} label="Vehicles" value="VEHICLES" />
          <Tab icon={<RouteIcon />} label="Routes & Stops" value="ROUTES" />
          <Tab icon={<AppIcon />} label="Applications" value="APPLICATIONS" />
          <Tab icon={<SubscriptionIcon />} label="Subscriptions" value="SUBSCRIPTIONS" />
          <Tab icon={<LiveMapIcon />} label="Live Tracking" value="TRACKING" />
          <Tab icon={<MaintenanceIcon />} label="Maintenance" value="MAINTENANCE" />
          <Tab icon={<FuelIcon />} label="Fuel Logs" value="FUEL" />
          <Tab icon={<IncidentIcon />} label="Incidents" value="INCIDENTS" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      {tab === 'DASHBOARD' && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'info.light', color: 'white' }}>
              <CardContent>
                <Typography variant="subtitle2">Total Vehicles</Typography>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{vehicles.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'success.light', color: 'white' }}>
              <CardContent>
                <Typography variant="subtitle2">Active Routes</Typography>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{routes.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'warning.light', color: 'white' }}>
              <CardContent>
                <Typography variant="subtitle2">Active Subscriptions</Typography>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{subscriptions.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'error.light', color: 'white' }}>
              <CardContent>
                <Typography variant="subtitle2">Unresolved Incidents</Typography>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{incidents.filter(i => i.status === 'OPEN').length}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {tab === 'VEHICLES' && (
        <Box>
          <Box display="flex" justifyContent="flex-end" mb={2}>
            <Button variant="contained" startIcon={<TransportIcon />} onClick={() => setOpenVehicleDlg(true)}>
              Setup Vehicle
            </Button>
          </Box>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Vehicle Code</TableCell>
                  <TableCell>Registration Number</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Manufacturer</TableCell>
                  <TableCell>Capacity</TableCell>
                  <TableCell>GPS Device ID</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {vehicles.map((v) => (
                  <TableRow key={v.id}>
                    <TableCell>{v.vehicleCode}</TableCell>
                    <TableCell>{v.registrationNumber}</TableCell>
                    <TableCell><Chip label={v.vehicleType} size="small" /></TableCell>
                    <TableCell>{v.manufacturer} {v.model}</TableCell>
                    <TableCell>{v.seatingCapacity} seats</TableCell>
                    <TableCell>{v.gpsDeviceId}</TableCell>
                    <TableCell>
                      <Chip
                        label={v.status}
                        color={v.status === 'ACTIVE' ? 'success' : v.status === 'MAINTENANCE' ? 'warning' : 'default'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {tab === 'ROUTES' && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Routes Directory</Typography>
              <Button variant="outlined" startIcon={<RouteIcon />} onClick={() => setOpenRouteDlg(true)}>Add Route</Button>
            </Box>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Code</TableCell>
                    <TableCell>Route Name</TableCell>
                    <TableCell>Origin / Destination</TableCell>
                    <TableCell>Est Distance / Time</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {routes.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell>{r.code}</TableCell>
                      <TableCell>{r.name}</TableCell>
                      <TableCell>{r.origin} ➔ {r.destination}</TableCell>
                      <TableCell>{r.estimatedDistanceKm} km / {r.estimatedDurationMinutes} mins</TableCell>
                      <TableCell><Chip label={r.status} color="success" size="small" /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>

          <Grid item xs={12} md={5}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Stops Directory</Typography>
              <Button variant="outlined" startIcon={<StopIcon />} onClick={() => setOpenStopDlg(true)}>Add Stop</Button>
            </Box>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Code</TableCell>
                    <TableCell>Stop Name</TableCell>
                    <TableCell>Coordinates</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {stops.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell>{s.code}</TableCell>
                      <TableCell>{s.name}</TableCell>
                      <TableCell>{s.latitude.toFixed(4)}, {s.longitude.toFixed(4)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>
      )}

      {tab === 'APPLICATIONS' && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Applications Queue</Typography>
            <Button variant="contained" startIcon={<AppIcon />} onClick={() => setOpenAppDlg(true)}>Apply for Pass</Button>
          </Box>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Applicant</TableCell>
                  <TableCell>Route Code</TableCell>
                  <TableCell>Pickup Stop</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {applications.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>{a.applicantName}</TableCell>
                    <TableCell>{a.routeCode}</TableCell>
                    <TableCell>{a.pickupStop}</TableCell>
                    <TableCell>
                      <Chip
                        label={a.status}
                        color={a.status === 'APPROVED' ? 'success' : a.status === 'SUBMITTED' ? 'info' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {a.status === 'SUBMITTED' && (
                        <Box display="flex" gap={1}>
                          <Button size="small" variant="contained" color="success" onClick={() => handleReviewApp(a.id, 'APPROVED')}>Approve</Button>
                          <Button size="small" variant="outlined" color="error" onClick={() => handleReviewApp(a.id, 'REJECTED')}>Reject</Button>
                        </Box>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {tab === 'SUBSCRIPTIONS' && (
        <Box>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>Active Passes & Subscriptions</Typography>
          <Grid container spacing={3}>
            {subscriptions.map((sub) => (
              <Grid item xs={12} sm={6} md={4} key={sub.id}>
                <Card sx={{ borderLeft: '5px solid #2e7d32' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>{sub.userName}</Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2">Route: {sub.routeCode}</Typography>
                    <Typography variant="body2">Pickup: {sub.pickupStop}</Typography>
                    <Typography variant="body2">Valid Until: {sub.endDate}</Typography>
                    <Box mt={2} display="flex" justifyContent="space-between" alignItems="center">
                      <Chip label={sub.status} color="success" size="small" />
                      <Chip label="Opaque Token Generated" variant="outlined" size="small" />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {tab === 'TRACKING' && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 4, height: 350, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', bgcolor: 'grey.100' }}>
              <LiveMapIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>Simulated GPS Map View</Typography>
              <Typography variant="body2" color="textSecondary" align="center">
                Currently tracking 1 active shuttle. [SIMULATED DEMO DATA fallbacks mapped to Bangalore, City limits]
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>Trips Live Status</Typography>
                <Divider sx={{ mb: 2 }} />
                {trips.map((t) => (
                  <Box key={t.id} mb={2}>
                    <Typography variant="subtitle2">Route: {t.routeCode} ({t.vehicleCode})</Typography>
                    <Typography variant="body2" color="error">Status: {t.status} (Delayed by {t.delayMinutes} mins)</Typography>
                    <Typography variant="body2">Scheduled: {t.scheduledStartAt} | Actual: {t.actualStartAt}</Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {tab === 'MAINTENANCE' && (
        <Box>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>Maintenance Log</Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Vehicle Code</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Odometer/Scheduled Date</TableCell>
                  <TableCell>Estimated Cost</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {maintenances.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell>{m.vehicleCode}</TableCell>
                    <TableCell>{m.maintenanceType}</TableCell>
                    <TableCell>{m.scheduledDate}</TableCell>
                    <TableCell>₹{m.estimatedCost.toFixed(2)}</TableCell>
                    <TableCell><Chip label={m.status} color="warning" size="small" /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {tab === 'FUEL' && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Fuel Purchase Registry</Typography>
            <Button variant="outlined" startIcon={<FuelIcon />} onClick={() => setOpenFuelDlg(true)}>Record Fuel Entry</Button>
          </Box>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Vehicle Code</TableCell>
                  <TableCell>Fill Date</TableCell>
                  <TableCell>Quantity (Litres)</TableCell>
                  <TableCell>Total Amount</TableCell>
                  <TableCell>Odometer reading</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {fuelLogs.map((f) => (
                  <TableRow key={f.id}>
                    <TableCell>{f.vehicleCode}</TableCell>
                    <TableCell>{f.filledAt}</TableCell>
                    <TableCell>{f.quantityLitres} L</TableCell>
                    <TableCell>₹{f.totalAmount.toFixed(2)}</TableCell>
                    <TableCell>{f.odometerKm} km</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {tab === 'INCIDENTS' && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Security & Incident Log</Typography>
            <Button variant="contained" color="error" startIcon={<IncidentIcon />} onClick={() => setOpenIncidentDlg(true)}>Report Incident</Button>
          </Box>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Vehicle Code</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Occurred At</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {incidents.map((i) => (
                  <TableRow key={i.id}>
                    <TableCell>{i.vehicleCode}</TableCell>
                    <TableCell>{i.type}</TableCell>
                    <TableCell><Chip label={i.severity} color="error" size="small" /></TableCell>
                    <TableCell>{i.description}</TableCell>
                    <TableCell>{i.occurredAt}</TableCell>
                    <TableCell><Chip label={i.status} color="error" size="small" /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* --- DIALOGS --- */}
      <Dialog open={openVehicleDlg} onClose={() => setOpenVehicleDlg(false)}>
        <DialogTitle>Setup Vehicle Profile</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2, minWidth: 350 }}>
          <TextField label="Registration Number" variant="outlined" value={newVehicle.registrationNumber} onChange={(e) => setNewVehicle({ ...newVehicle, registrationNumber: e.target.value })} />
          <TextField label="Vehicle Code" variant="outlined" value={newVehicle.vehicleCode} onChange={(e) => setNewVehicle({ ...newVehicle, vehicleCode: e.target.value })} />
          <TextField label="Manufacturer" variant="outlined" value={newVehicle.manufacturer} onChange={(e) => setNewVehicle({ ...newVehicle, manufacturer: e.target.value })} />
          <TextField label="Model" variant="outlined" value={newVehicle.model} onChange={(e) => setNewVehicle({ ...newVehicle, model: e.target.value })} />
          <TextField label="Seating Capacity" type="number" variant="outlined" value={newVehicle.seatingCapacity} onChange={(e) => setNewVehicle({ ...newVehicle, seatingCapacity: parseInt(e.target.value) || 40 })} />
          <TextField label="GPS Device ID" variant="outlined" value={newVehicle.gpsDeviceId} onChange={(e) => setNewVehicle({ ...newVehicle, gpsDeviceId: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenVehicleDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddVehicle}>Save</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openRouteDlg} onClose={() => setOpenRouteDlg(false)}>
        <DialogTitle>Add Loop Route</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2, minWidth: 350 }}>
          <TextField label="Route Name" variant="outlined" value={newRoute.name} onChange={(e) => setNewRoute({ ...newRoute, name: e.target.value })} />
          <TextField label="Route Code" variant="outlined" value={newRoute.code} onChange={(e) => setNewRoute({ ...newRoute, code: e.target.value })} />
          <TextField label="Origin Stop" variant="outlined" value={newRoute.origin} onChange={(e) => setNewRoute({ ...newRoute, origin: e.target.value })} />
          <TextField label="Destination Stop" variant="outlined" value={newRoute.destination} onChange={(e) => setNewRoute({ ...newRoute, destination: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRouteDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddRoute}>Save</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openStopDlg} onClose={() => setOpenStopDlg(false)}>
        <DialogTitle>Setup Route Stop Point</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2, minWidth: 350 }}>
          <TextField label="Stop Name" variant="outlined" value={newStop.name} onChange={(e) => setNewStop({ ...newStop, name: e.target.value })} />
          <TextField label="Stop Code" variant="outlined" value={newStop.code} onChange={(e) => setNewStop({ ...newStop, code: e.target.value })} />
          <TextField label="Address" variant="outlined" value={newStop.address} onChange={(e) => setNewStop({ ...newStop, address: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenStopDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddStop}>Save</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openAppDlg} onClose={() => setOpenAppDlg(false)}>
        <DialogTitle>Request Transport Pass</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2, minWidth: 350 }}>
          <FormControl fullWidth>
            <InputLabel>Route</InputLabel>
            <Select value={newApp.routeId} label="Route" onChange={(e) => setNewApp({ ...newApp, routeId: e.target.value })}>
              {routes.map(r => <MenuItem key={r.id} value={r.code}>{r.name} ({r.code})</MenuItem>)}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAppDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => {
            if (!newApp.routeId) return;
            setApplications([...applications, {
              id: `app-${Date.now()}`,
              applicantName: 'Samantha Student',
              routeCode: newApp.routeId,
              pickupStop: 'Metro Junction',
              dropStop: 'Main Campus',
              status: 'SUBMITTED',
              submittedAt: new Date().toISOString().split('T')[0]
            }]);
            setOpenAppDlg(false);
          }}>Submit</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openIncidentDlg} onClose={() => setOpenIncidentDlg(false)}>
        <DialogTitle>Report Incident / Hazard</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2, minWidth: 350 }}>
          <FormControl fullWidth>
            <InputLabel>Vehicle</InputLabel>
            <Select value={newIncident.vehicleId} label="Vehicle" onChange={(e) => setNewIncident({ ...newIncident, vehicleId: e.target.value })}>
              {vehicles.map(v => <MenuItem key={v.id} value={v.id}>{v.vehicleCode}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Type</InputLabel>
            <Select value={newIncident.type} label="Type" onChange={(e) => setNewIncident({ ...newIncident, type: e.target.value })}>
              <MenuItem value="BREAKDOWN">Breakdown</MenuItem>
              <MenuItem value="ACCIDENT">Accident</MenuItem>
              <MenuItem value="DELAY">Traffic Delay</MenuItem>
              <MenuItem value="SECURITY">Security Incident</MenuItem>
            </Select>
          </FormControl>
          <TextField label="Description" variant="outlined" multiline rows={3} value={newIncident.description} onChange={(e) => setNewIncident({ ...newIncident, description: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenIncidentDlg(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleAddIncident}>Report</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openFuelDlg} onClose={() => setOpenFuelDlg(false)}>
        <DialogTitle>Record Fuel Fill</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2, minWidth: 350 }}>
          <FormControl fullWidth>
            <InputLabel>Vehicle</InputLabel>
            <Select value={newFuel.vehicleId} label="Vehicle" onChange={(e) => setNewFuel({ ...newFuel, vehicleId: e.target.value })}>
              {vehicles.map(v => <MenuItem key={v.id} value={v.id}>{v.vehicleCode}</MenuItem>)}
            </Select>
          </FormControl>
          <TextField label="Quantity (Litres)" type="number" variant="outlined" value={newFuel.quantityLitres} onChange={(e) => setNewFuel({ ...newFuel, quantityLitres: parseFloat(e.target.value) || 0.0 })} />
          <TextField label="Total Cost" type="number" variant="outlined" value={newFuel.totalAmount} onChange={(e) => setNewFuel({ ...newFuel, totalAmount: parseFloat(e.target.value) || 0.0 })} />
          <TextField label="Odometer Reading (km)" type="number" variant="outlined" value={newFuel.odometerKm} onChange={(e) => setNewFuel({ ...newFuel, odometerKm: parseInt(e.target.value) || 0 })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenFuelDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddFuel}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
