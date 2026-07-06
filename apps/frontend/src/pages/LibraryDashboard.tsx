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
  DialogActions
} from '@mui/material';
import {
  MenuBook as BookIcon,
  People as PeopleIcon,
  AssignmentTurnedIn as IssueIcon,
  SwapHoriz as CirculationIcon,
  AttachMoney as FineIcon,
  TrendingUp as AnalyticsIcon
} from '@mui/icons-material';

export const LibraryDashboard: React.FC = () => {
  const [tab, setTab] = useState<string>('CATALOG');
  const [books, setBooks] = useState<any[]>([
    { id: 'b-1', isbn: '9780134685991', title: 'Effective Java', author: 'Joshua Bloch', category: 'Programming', copies: 3, available: 2 },
    { id: 'b-2', isbn: '9780132350884', title: 'Clean Code', author: 'Robert C. Martin', category: 'Software Engineering', copies: 4, available: 3 }
  ]);
  const [copies, setCopies] = useState<any[]>([
    { id: 'c-1', barcode: 'BAR-EJ-01', accession: 'ACC-EJ-01', bookTitle: 'Effective Java', status: 'AVAILABLE', condition: 'GOOD' },
    { id: 'c-2', barcode: 'BAR-EJ-02', accession: 'ACC-EJ-02', bookTitle: 'Effective Java', status: 'ISSUED', condition: 'GOOD' },
    { id: 'c-3', barcode: 'BAR-CC-01', accession: 'ACC-CC-01', bookTitle: 'Clean Code', status: 'AVAILABLE', condition: 'GOOD' }
  ]);
  const [memberships] = useState<any[]>([
    { id: 'm-1', number: 'MEMB-STUD-01', userName: 'Samantha Vance', type: 'STUDENT', status: 'ACTIVE' },
    { id: 'm-2', number: 'MEMB-STUD-02', userName: 'Marcus Vance', type: 'STUDENT', status: 'ACTIVE' }
  ]);
  const [loans, setLoans] = useState<any[]>([
    { id: 'l-1', barcode: 'BAR-EJ-02', memberNumber: 'MEMB-STUD-01', bookTitle: 'Effective Java', issuedAt: '2026-07-01', dueAt: '2026-07-15', status: 'ACTIVE' }
  ]);
  const [fines, setFines] = useState<any[]>([
    { id: 'f-1', memberNumber: 'MEMB-STUD-01', amount: 50.00, reason: 'OVERDUE', status: 'PENDING' }
  ]);

  // Dialog States
  const [openBookDlg, setOpenBookDlg] = useState(false);
  const [openIssueDlg, setOpenIssueDlg] = useState(false);
  const [openReturnDlg, setOpenReturnDlg] = useState(false);

  // Form Fields
  const [newBook, setNewBook] = useState({ isbn: '', title: '', author: '', category: '' });
  const [issueFields, setIssueFields] = useState({ membershipNumber: '', barcode: '' });
  const [returnBarcode, setReturnBarcode] = useState('');

  const handleAddBook = () => {
    if (!newBook.isbn || !newBook.title) return;
    setBooks([...books, {
      id: `b-${Date.now()}`,
      isbn: newBook.isbn,
      title: newBook.title,
      author: newBook.author,
      category: newBook.category,
      copies: 1,
      available: 1
    }]);
    setOpenBookDlg(false);
    setNewBook({ isbn: '', title: '', author: '', category: '' });
  };

  const handleIssueBook = () => {
    if (!issueFields.membershipNumber || !issueFields.barcode) return;
    setLoans([...loans, {
      id: `l-${Date.now()}`,
      barcode: issueFields.barcode,
      memberNumber: issueFields.membershipNumber,
      bookTitle: 'Clean Code',
      issuedAt: '2026-07-06',
      dueAt: '2026-07-20',
      status: 'ACTIVE'
    }]);
    setCopies(copies.map(c => c.barcode === issueFields.barcode ? { ...c, status: 'ISSUED' } : c));
    setOpenIssueDlg(false);
    setIssueFields({ membershipNumber: '', barcode: '' });
  };

  const handleReturnBook = () => {
    if (!returnBarcode) return;
    setLoans(loans.map(l => l.barcode === returnBarcode ? { ...l, status: 'RETURNED' } : l));
    setCopies(copies.map(c => c.barcode === returnBarcode ? { ...c, status: 'AVAILABLE' } : c));
    setOpenReturnDlg(false);
    setReturnBarcode('');
  };

  return (
    <Box sx={{ p: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary">Smart Library Operating Console</Typography>
          <Typography variant="subtitle1" color="textSecondary">Manage inventory acquisitions, memberships, checkouts, and fine settlements.</Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button variant="outlined" startIcon={<IssueIcon />} onClick={() => setOpenReturnDlg(true)}>
            Return Copy
          </Button>
          <Button variant="contained" startIcon={<CirculationIcon />} onClick={() => setOpenIssueDlg(true)}>
            Issue Book
          </Button>
        </Box>
      </Box>

      {/* Tabs Menu */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tab} onChange={(_, val) => setTab(val)} textColor="primary" indicatorColor="primary">
          <Tab value="CATALOG" label="Bibliographic Catalog" icon={<BookIcon />} iconPosition="start" />
          <Tab value="COPIES" label="Physical Inventory" icon={<IssueIcon />} iconPosition="start" />
          <Tab value="MEMBERSHIP" label="Memberships Registry" icon={<PeopleIcon />} iconPosition="start" />
          <Tab value="LOANS" label="Active Loans" icon={<CirculationIcon />} iconPosition="start" />
          <Tab value="FINES" label="Fines & Penalties" icon={<FineIcon />} iconPosition="start" />
          <Tab value="ANALYTICS" label="System Analytics" icon={<AnalyticsIcon />} iconPosition="start" />
        </Tabs>
      </Box>

      {/* Tab content 1: CATALOG */}
      {tab === 'CATALOG' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" fontWeight="bold">Cataloged Books</Typography>
            <Button variant="contained" size="small" onClick={() => setOpenBookDlg(true)}>Acquire Book Title</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ISBN-13</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Author</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Total Copies</TableCell>
                  <TableCell>Available</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {books.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell>{b.isbn}</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>{b.title}</TableCell>
                    <TableCell>{b.author}</TableCell>
                    <TableCell>{b.category}</TableCell>
                    <TableCell>{b.copies}</TableCell>
                    <TableCell>
                      <Chip label={`${b.available} In Stock`} color={b.available > 0 ? "success" : "error"} size="small" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Tab content 2: COPIES */}
      {tab === 'COPIES' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Inventory Copy Register</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Barcode</TableCell>
                  <TableCell>Accession Number</TableCell>
                  <TableCell>Book Title</TableCell>
                  <TableCell>Condition</TableCell>
                  <TableCell>Circulation Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {copies.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{c.barcode}</TableCell>
                    <TableCell>{c.accession}</TableCell>
                    <TableCell>{c.bookTitle}</TableCell>
                    <TableCell><Chip label={c.condition} size="small" /></TableCell>
                    <TableCell>
                      <Chip
                        label={c.status}
                        color={c.status === 'AVAILABLE' ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Tab content 3: MEMBERSHIPS */}
      {tab === 'MEMBERSHIP' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Active Library Memberships</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Membership Number</TableCell>
                  <TableCell>Member Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {memberships.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{m.number}</TableCell>
                    <TableCell>{m.userName}</TableCell>
                    <TableCell>{m.type}</TableCell>
                    <TableCell><Chip label={m.status} color="success" size="small" /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Tab content 4: LOANS */}
      {tab === 'LOANS' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Outstanding Active Loans</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Barcode</TableCell>
                  <TableCell>Book Title</TableCell>
                  <TableCell>Borrower ID</TableCell>
                  <TableCell>Issued Date</TableCell>
                  <TableCell>Return Due Date</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loans.map((l) => (
                  <TableRow key={l.id}>
                    <TableCell>{l.barcode}</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>{l.bookTitle}</TableCell>
                    <TableCell>{l.memberNumber}</TableCell>
                    <TableCell>{l.issuedAt}</TableCell>
                    <TableCell>{l.dueAt}</TableCell>
                    <TableCell><Chip label={l.status} color="primary" size="small" /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Tab content 5: FINES */}
      {tab === 'FINES' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Outstanding Penalties & Waiving Panel</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Borrower ID</TableCell>
                  <TableCell>Assessed Penalty</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Payment Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {fines.map((f) => (
                  <TableRow key={f.id}>
                    <TableCell>{f.memberNumber}</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', color: 'error.main' }}>{f.amount} INR</TableCell>
                    <TableCell>{f.reason}</TableCell>
                    <TableCell><Chip label={f.status} color="warning" size="small" /></TableCell>
                    <TableCell>
                      <Button variant="outlined" color="success" size="small" sx={{ mr: 1 }} onClick={() => setFines(fines.map(fi => fi.id === f.id ? { ...fi, status: 'PAID' } : fi))}>
                        Settle Fine
                      </Button>
                      <Button variant="outlined" color="secondary" size="small" onClick={() => setFines(fines.map(fi => fi.id === f.id ? { ...fi, status: 'WAIVED' } : fi))}>
                        Waive
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Tab content 6: ANALYTICS */}
      {tab === 'ANALYTICS' && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={4}>
            <Card sx={{ borderRadius: 3 }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="textSecondary">Active Inventory Volumes</Typography>
                <Typography variant="h3" fontWeight="bold" color="primary">7 Volumes</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card sx={{ borderRadius: 3 }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="textSecondary">Active Loans Ratio</Typography>
                <Typography variant="h3" fontWeight="bold" color="success">14.2%</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card sx={{ borderRadius: 3 }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="textSecondary">Overdue Fines Outstanding</Typography>
                <Typography variant="h3" fontWeight="bold" color="error">50.00 INR</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Dialog: Acquire Book */}
      <Dialog open={openBookDlg} onClose={() => setOpenBookDlg(false)}>
        <DialogTitle sx={{ fontWeight: 'bold' }}>Acquire Book Title</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 320, pt: 1 }}>
          <TextField label="ISBN-13" size="small" fullWidth value={newBook.isbn} onChange={e => setNewBook({ ...newBook, isbn: e.target.value })} />
          <TextField label="Title" size="small" fullWidth value={newBook.title} onChange={e => setNewBook({ ...newBook, title: e.target.value })} />
          <TextField label="Author" size="small" fullWidth value={newBook.author} onChange={e => setNewBook({ ...newBook, author: e.target.value })} />
          <TextField label="Category" size="small" fullWidth value={newBook.category} onChange={e => setNewBook({ ...newBook, category: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenBookDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddBook}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Issue Copy */}
      <Dialog open={openIssueDlg} onClose={() => setOpenIssueDlg(false)}>
        <DialogTitle sx={{ fontWeight: 'bold' }}>Issue Book Copy</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 320, pt: 1 }}>
          <TextField label="Membership Number" size="small" fullWidth value={issueFields.membershipNumber} onChange={e => setIssueFields({ ...issueFields, membershipNumber: e.target.value })} />
          <TextField label="Barcode / Accession" size="small" fullWidth value={issueFields.barcode} onChange={e => setIssueFields({ ...issueFields, barcode: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenIssueDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleIssueBook}>Complete Checkout</Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Return Copy */}
      <Dialog open={openReturnDlg} onClose={() => setOpenReturnDlg(false)}>
        <DialogTitle sx={{ fontWeight: 'bold' }}>Return Book Copy</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 320, pt: 1 }}>
          <TextField label="Scan Barcode / Accession" size="small" fullWidth value={returnBarcode} onChange={e => setReturnBarcode(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenReturnDlg(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleReturnBook}>Verify Return</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LibraryDashboard;
