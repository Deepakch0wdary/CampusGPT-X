import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Typography, 
  Paper, 
  Box, 
  Button, 
  CircularProgress, 
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import { ArrowBack as BackIcon, UploadFile as FileIcon } from '@mui/icons-material';

export const ImportUsers: React.FC = () => {
  const navigate = useNavigate();
  
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [successCount, setSuccessCount] = useState<number | null>(null);
  const [errorsList, setErrorsList] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMsg(null);
      setSuccessCount(null);
      setErrorsList([]);
    }
  };

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg('Please choose an Excel spreadsheet file to import.');
      return;
    }

    setImporting(true);
    setErrorMsg(null);
    setSuccessCount(null);
    setErrorsList([]);

    const token = localStorage.getItem('access_token');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/users/import', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || 'Bulk import failed.');
      }

      setSuccessCount(data.imported);
      setErrorsList(data.errors || []);
      setFile(null);
    } catch (err: any) {
      setErrorMsg(err.message || 'An error occurred during sheet parsing.');
    } finally {
      setImporting(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 680, mx: 'auto' }}>
      <Button startIcon={<BackIcon />} onClick={() => navigate('/dashboard')} sx={{ mb: 4 }}>
        Back to Dashboard
      </Button>

      <Typography variant="h4" sx={{ fontFamily: 'Outfit', fontWeight: 800, mb: 4 }}>
        Excel Spreadsheet Bulk Import
      </Typography>

      <Paper sx={{ p: 4, bgcolor: 'background.paper', mb: 4 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Upload a <strong>.xlsx</strong> or <strong>.xls</strong> spreadsheet containing campus users. 
          The first row must declare headers: <strong>Name</strong>, <strong>Email</strong>, and <strong>Role</strong>. 
          Optional fields: <em>DepartmentCode</em>, <em>SectionCode</em>, <em>DesignationCode</em>.
        </Typography>

        {errorMsg && <Alert severity="error" sx={{ mb: 3 }}>{errorMsg}</Alert>}
        
        {successCount !== null && (
          <Alert severity={errorsList.length === 0 ? 'success' : 'warning'} sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
              Spreadsheet Processing Complete!
            </Typography>
            <Typography variant="body2">Successfully created {successCount} user account(s).</Typography>
            {errorsList.length > 0 && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                * Bypassed {errorsList.length} rows due to validation conflicts (details listed below).
              </Typography>
            )}
          </Alert>
        )}

        <form onSubmit={handleImportSubmit}>
          <Box sx={{ border: '2px dashed rgba(255,255,255,0.12)', p: 4, borderRadius: 2, textAlign: 'center', mb: 3, cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }}>
            <input
              type="file"
              accept=".xlsx, .xls"
              onChange={handleFileChange}
              id="spreadsheet-file-input"
              style={{ display: 'none' }}
            />
            <label htmlFor="spreadsheet-file-input" style={{ cursor: 'pointer' }}>
              <FileIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1">
                {file ? file.name : 'Click to select Excel spreadsheet file...'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Supports Excel spreadsheets up to 10MB
              </Typography>
            </label>
          </Box>

          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={importing || !file}
            sx={{ height: 48, px: 4 }}
          >
            {importing ? <CircularProgress size={24} color="inherit" /> : 'Execute Bulk Import'}
          </Button>
        </form>
      </Paper>

      {/* Row-Level Errors Report */}
      {errorsList.length > 0 && (
        <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
          <Typography variant="h6" color="warning.main" sx={{ fontWeight: 700, mb: 2 }}>
            Row Import Diagnostics ({errorsList.length} exceptions)
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <List sx={{ maxHeight: 240, overflow: 'auto' }}>
            {errorsList.map((err, idx) => (
              <ListItem key={idx} sx={{ py: 0.5 }}>
                <ListItemText 
                  primary={err} 
                  primaryTypographyProps={{ fontSize: 13, color: 'error.light' }} 
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
};
export default ImportUsers;
