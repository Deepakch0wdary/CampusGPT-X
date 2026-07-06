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
  CardContent
} from '@mui/material';
import {
  Payment as PayIcon,
  Receipt as ReceiptIcon
} from '@mui/icons-material';

export const FeeDashboard: React.FC = () => {
  const [role, setRole] = useState<string>('FINANCE_OFFICE');
  const [tab, setTab] = useState<'STRUCTURES' | 'INVOICES' | 'PAYMENTS' | 'SCHOLARSHIPS' | 'ANALYTICS'>('INVOICES');

  // Master fee states
  const [structures] = useState<any[]>([
    { id: 'fs-1', name: 'B.Tech CSE Core Structure', currency: 'INR', total: 60000.00 }
  ]);

  const [invoices, setInvoices] = useState<any[]>([
    { id: 'inv-1', invoiceNumber: 'INV-2026-001', studentName: 'Deepak Chowdary', total: 60000.00, paid: 20000.00, balance: 40000.00, status: 'PARTIALLY_PAID' }
  ]);

  const [payments, setPayments] = useState<any[]>([
    { id: 'pay-1', paymentNumber: 'PAY-2026-001', studentName: 'Deepak Chowdary', amount: 20000.00, method: 'UPI', status: 'SUCCESS', date: '2026-07-06' }
  ]);

  const [scholarships] = useState<any[]>([
    { id: 'sch-1', name: 'Merit Waiver Waiver', type: 'Merit Scholarship', amount: 15000.00, valid: '2026-06 to 2027-05' }
  ]);

  // Form states
  const [payOpen, setPayOpen] = useState(false);
  const [selectedInv, setSelectedInv] = useState<any>(null);
  const [payAmount, setPayAmount] = useState<number>(10000);
  const [payMethod, setPayMethod] = useState<string>('UPI');

  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleProcessPayment = () => {
    if (!selectedInv) return;
    if (payAmount > selectedInv.balance) {
      setFeedback({ type: 'error', text: 'Payment amount exceeds outstanding balance.' });
      return;
    }

    const payNum = `PAY-2026-00${payments.length + 1}`;
    const newPay = {
      id: `pay-${Date.now()}`,
      paymentNumber: payNum,
      studentName: selectedInv.studentName,
      amount: payAmount,
      method: payMethod,
      status: 'SUCCESS',
      date: new Date().toISOString().split('T')[0]
    };

    setPayments([newPay, ...payments]);
    setInvoices(invoices.map(i => {
      if (i.id === selectedInv.id) {
        const newPaid = i.paid + payAmount;
        const newBal = i.total - newPaid;
        return {
          ...i,
          paid: newPaid,
          balance: newBal,
          status: newBal <= 0 ? 'PAID' : 'PARTIALLY_PAID'
        };
      }
      return i;
    }));

    setFeedback({ type: 'success', text: `Payment of ${payAmount} processed. Transaction: ${payNum}` });
    setPayOpen(false);
  };

  return (
    <Box sx={{ p: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="primary">Fee & Payment Desk</Typography>
          <Typography variant="subtitle1" color="textSecondary">Configure structures, review invoices, process payments, and verify receipts.</Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Role Context</InputLabel>
          <Select value={role} onChange={(e) => setRole(e.target.value)} label="Role Context">
            <MenuItem value="FINANCE_OFFICE">Finance Officer</MenuItem>
            <MenuItem value="STUDENT">Student Candidate</MenuItem>
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
          <Tab value="INVOICES" label="Fee Invoices" />
          <Tab value="STRUCTURES" label="Fee Structures" />
          <Tab value="PAYMENTS" label="Payment Records" />
          <Tab value="SCHOLARSHIPS" label="Scholarships Portal" />
          <Tab value="ANALYTICS" label="Revenue Analytics" />
        </Tabs>
      </Box>

      {/* TAB 1: INVOICES */}
      {tab === 'INVOICES' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Invoices Registry</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Invoice Number</TableCell>
                  <TableCell>Student Name</TableCell>
                  <TableCell>Total Amount</TableCell>
                  <TableCell>Paid Amount</TableCell>
                  <TableCell>Outstanding Balance</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Pay Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {invoices.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{inv.invoiceNumber}</TableCell>
                    <TableCell>{inv.studentName}</TableCell>
                    <TableCell>{inv.total} INR</TableCell>
                    <TableCell>{inv.paid} INR</TableCell>
                    <TableCell sx={{ color: 'error.main', fontWeight: 'bold' }}>{inv.balance} INR</TableCell>
                    <TableCell>
                      <Chip
                        label={inv.status}
                        color={inv.status === 'PAID' ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      {inv.balance > 0 && (
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<PayIcon />}
                          onClick={() => { setSelectedInv(inv); setPayOpen(true); }}
                        >
                          Collect Payment
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

      {/* TAB 2: STRUCTURES */}
      {tab === 'STRUCTURES' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Fee Structure Configurations</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Structure Name</TableCell>
                  <TableCell>Currency</TableCell>
                  <TableCell>Mandatory Total</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {structures.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{s.name}</TableCell>
                    <TableCell>{s.currency}</TableCell>
                    <TableCell>{s.total} INR</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 3: PAYMENT HISTORY */}
      {tab === 'PAYMENTS' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Successful Transactions & Receipts</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Payment ID</TableCell>
                  <TableCell>Student Candidate</TableCell>
                  <TableCell>Collected Amount</TableCell>
                  <TableCell>Payment Method</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Verification</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {payments.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{p.paymentNumber}</TableCell>
                    <TableCell>{p.studentName}</TableCell>
                    <TableCell>{p.amount} INR</TableCell>
                    <TableCell>{p.method}</TableCell>
                    <TableCell>{p.date}</TableCell>
                    <TableCell>
                      <Chip icon={<ReceiptIcon />} label="Download Receipt" size="small" color="success" onClick={() => {}} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 4: SCHOLARSHIPS */}
      {tab === 'SCHOLARSHIPS' && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Active Scholarships / Fee waivers</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Scholarship Name</TableCell>
                  <TableCell>Grant Type</TableCell>
                  <TableCell>Awarded Amount</TableCell>
                  <TableCell>Valid Span</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {scholarships.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell sx={{ fontWeight: 'bold' }}>{s.name}</TableCell>
                    <TableCell>{s.type}</TableCell>
                    <TableCell>{s.amount} INR</TableCell>
                    <TableCell>{s.valid}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* TAB 5: REVENUE ANALYTICS */}
      {tab === 'ANALYTICS' && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={4}>
            <Card sx={{ bgcolor: 'info.light', color: 'info.contrastText', borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6">Total Invoiced</Typography>
                <Typography variant="h3" fontWeight="bold">60,000 INR</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card sx={{ bgcolor: 'success.light', color: 'success.contrastText', borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6">Total Collected</Typography>
                <Typography variant="h3" fontWeight="bold">20,000 INR</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card sx={{ bgcolor: 'error.light', color: 'error.contrastText', borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6">Outstanding Balance</Typography>
                <Typography variant="h3" fontWeight="bold">40,000 INR</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* DIALOG: COLLECT PAYMENT */}
      <Dialog open={payOpen} onClose={() => setPayOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>Process Payment</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Payment Amount (INR)"
                type="number"
                fullWidth
                value={payAmount}
                onChange={(e) => setPayAmount(Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Payment Method</InputLabel>
                <Select value={payMethod} onChange={(e) => setPayMethod(e.target.value)} label="Payment Method">
                  <MenuItem value="CASH">Cash Deposit</MenuItem>
                  <MenuItem value="UPI">UPI Transfer</MenuItem>
                  <MenuItem value="CREDIT_CARD">Credit Card</MenuItem>
                  <MenuItem value="DEBIT_CARD">Debit Card</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPayOpen(false)}>Cancel</Button>
          <Button color="primary" variant="contained" onClick={handleProcessPayment}>Confirm Payment</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FeeDashboard;
