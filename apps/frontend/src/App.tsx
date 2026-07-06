import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';
import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';
import ChangePassword from './pages/ChangePassword';
import UserDashboard from './pages/UserDashboard';
import UserDetails from './pages/UserDetails';
import ImportUsers from './pages/ImportUsers';
import NotFound from './pages/NotFound';
import Forbidden from './pages/Forbidden';
import ServerError from './pages/ServerError';
import AcademicDashboard from './pages/AcademicDashboard';
import StudentDashboard from './pages/StudentDashboard';
import FacultyDashboard from './pages/FacultyDashboard';
import TimetableDashboard from './pages/TimetableDashboard';
import AttendanceDashboard from './pages/AttendanceDashboard';
import QRAttendanceDashboard from './pages/QRAttendanceDashboard';
import FaceRecognitionDashboard from './pages/FaceRecognitionDashboard';
import AssignmentDashboard from './pages/AssignmentDashboard';
import ExamDashboard from './pages/ExamDashboard';
import ResultDashboard from './pages/ResultDashboard';
import AdmissionDashboard from './pages/AdmissionDashboard';
import FeeDashboard from './pages/FeeDashboard';
import ParentDashboard from './pages/ParentDashboard';
import LibraryDashboard from './pages/LibraryDashboard';

// Helper validators for local session tracking
const isAuthenticated = () => !!localStorage.getItem('access_token');

const isMasterAdmin = () => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return false;
  try {
    const user = JSON.parse(userStr);
    return user.role === 'MASTER_ADMIN';
  } catch {
    return false;
  }
};

const mustChangePassword = () => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return false;
  try {
    const user = JSON.parse(userStr);
    return !!user.mustChangePassword;
  } catch {
    return false;
  }
};

// Route Security Guards
const PrivateRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  if (mustChangePassword()) {
    return <Navigate to="/change-password" replace />;
  }
  return children;
};

const AdminRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  if (mustChangePassword()) {
    return <Navigate to="/change-password" replace />;
  }
  if (!isMasterAdmin()) {
    return <Navigate to="/" replace />;
  }
  return children;
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={
              isAuthenticated() ? <Navigate to="/" replace /> : <Login />
            } />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            
            {/* Password Force Route */}
            <Route path="/change-password" element={
              isAuthenticated() ? <ChangePassword /> : <Navigate to="/login" replace />
            } />

            {/* General Private Routes */}
            <Route path="/" element={
              <PrivateRoute>
                <Home />
              </PrivateRoute>
            } />

            <Route path="/academics" element={
              <PrivateRoute>
                <AcademicDashboard />
              </PrivateRoute>
            } />

            <Route path="/student-dashboard" element={
              <PrivateRoute>
                <StudentDashboard />
              </PrivateRoute>
            } />

            <Route path="/faculty-dashboard" element={
              <PrivateRoute>
                <FacultyDashboard />
              </PrivateRoute>
            } />

            <Route path="/timetable-dashboard" element={
              <PrivateRoute>
                <TimetableDashboard />
              </PrivateRoute>
            } />

            <Route path="/attendance-dashboard" element={
              <PrivateRoute>
                <AttendanceDashboard />
              </PrivateRoute>
            } />

            <Route path="/qr-attendance-dashboard" element={
              <PrivateRoute>
                <QRAttendanceDashboard />
              </PrivateRoute>
            } />

            <Route path="/face-recognition-dashboard" element={
              <PrivateRoute>
                <FaceRecognitionDashboard />
              </PrivateRoute>
            } />

            <Route path="/assignment-dashboard" element={
              <PrivateRoute>
                <AssignmentDashboard />
              </PrivateRoute>
            } />

            <Route path="/exam-dashboard" element={
              <PrivateRoute>
                <ExamDashboard />
              </PrivateRoute>
            } />

            <Route path="/result-dashboard" element={
              <PrivateRoute>
                <ResultDashboard />
              </PrivateRoute>
            } />

            <Route path="/admission-dashboard" element={
              <PrivateRoute>
                <AdmissionDashboard />
              </PrivateRoute>
            } />

            <Route path="/fee-dashboard" element={
              <PrivateRoute>
                <FeeDashboard />
              </PrivateRoute>
            } />

            <Route path="/parent-dashboard" element={
              <PrivateRoute>
                <ParentDashboard />
              </PrivateRoute>
            } />

            <Route path="/library-dashboard" element={
              <PrivateRoute>
                <LibraryDashboard />
              </PrivateRoute>
            } />

            {/* Admin Exclusive Routes */}
            <Route path="/dashboard" element={
              <AdminRoute>
                <UserDashboard />
              </AdminRoute>
            } />
            
            <Route path="/users/:id" element={
              <AdminRoute>
                <UserDetails />
              </AdminRoute>
            } />

            <Route path="/import-users" element={
              <AdminRoute>
                <ImportUsers />
              </AdminRoute>
            } />

            <Route path="/403" element={<Forbidden />} />
            <Route path="/500" element={<ServerError />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
};
export default App;
