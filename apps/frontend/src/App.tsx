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
import { ParentDashboard } from './pages/ParentDashboard';
import LibraryDashboard from './pages/LibraryDashboard';
import HostelDashboard from './pages/HostelDashboard';
import { TransportDashboard } from './pages/TransportDashboard';
import NotificationCenter from './pages/NotificationCenter';
import NotificationPreferences from './pages/NotificationPreferences';
import CommunicationDashboard from './pages/CommunicationDashboard';
import AnnouncementManager from './pages/AnnouncementManager';
import BroadcastManager from './pages/BroadcastManager';
import EmergencyAlerts from './pages/EmergencyAlerts';
import NotificationTemplates from './pages/NotificationTemplates';
import AcademicMentorDashboard from './pages/AcademicMentorDashboard';
import AcademicInsights from './pages/AcademicInsights';
import RiskAssessment from './pages/RiskAssessment';
import StudyRecommendations from './pages/StudyRecommendations';
import StudyPlanner from './pages/StudyPlanner';
import StudentGoals from './pages/StudentGoals';
import MentorStudentDashboard from './pages/MentorStudentDashboard';
import ParentAcademicInsights from './pages/ParentAcademicInsights';
import AcademicIntelligenceAdmin from './pages/AcademicIntelligenceAdmin';
import InterventionManager from './pages/InterventionManager';
import PlacementDashboard from './pages/PlacementDashboard';
import PlacementOpportunities from './pages/PlacementOpportunities';
import PlacementAdmin from './pages/PlacementAdmin';


// Intercept all API calls to catch 401 Unauthorized errors and clear stale sessions
const originalFetch = window.fetch;
window.fetch = async (...args) => {
  const response = await originalFetch(...args);
  if (response.status === 401) {
    const hasToken = !!localStorage.getItem('access_token');
    const isLoginRequest = typeof args[0] === 'string' && args[0].includes('/api/v1/auth/login');
    if (hasToken && !isLoginRequest) {
      localStorage.clear();
      window.dispatchEvent(new Event('storage'));
      window.location.href = '/login';
    }
  }
  return response;
};

// Helper validators for local session tracking with JWT expiration check
const isAuthenticated = () => {
  const token = localStorage.getItem('access_token');
  if (!token) return false;
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    // Decode base64 payload safely using atob
    const payload = JSON.parse(atob(parts[1]));
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp && payload.exp < now) {
      localStorage.clear();
      return false;
    }
    return true;
  } catch (e) {
    localStorage.clear();
    return false;
  }
};

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

            <Route path="/hostel-dashboard" element={
              <PrivateRoute>
                <HostelDashboard />
              </PrivateRoute>
            } />

            <Route path="/transport-dashboard" element={
              <PrivateRoute>
                <TransportDashboard />
              </PrivateRoute>
            } />

            <Route path="/notifications" element={
              <PrivateRoute>
                <NotificationCenter />
              </PrivateRoute>
            } />

            <Route path="/notification-preferences" element={
              <PrivateRoute>
                <NotificationPreferences />
              </PrivateRoute>
            } />

            <Route path="/academic-mentor" element={
              <PrivateRoute>
                <AcademicMentorDashboard />
              </PrivateRoute>
            } />
            <Route path="/placements" element={
              <PrivateRoute>
                <PlacementDashboard />
              </PrivateRoute>
            } />
            <Route path="/placements/opportunities" element={
              <PrivateRoute>
                <PlacementOpportunities />
              </PrivateRoute>
            } />
            <Route path="/placements/admin" element={
              <AdminRoute>
                <PlacementAdmin />
              </AdminRoute>
            } />

            <Route path="/academic-mentor/insights" element={
              <PrivateRoute>
                <AcademicInsights />
              </PrivateRoute>
            } />
            <Route path="/academic-mentor/risk" element={
              <PrivateRoute>
                <RiskAssessment />
              </PrivateRoute>
            } />
            <Route path="/academic-mentor/recommendations" element={
              <PrivateRoute>
                <StudyRecommendations />
              </PrivateRoute>
            } />
            <Route path="/academic-mentor/study-planner" element={
              <PrivateRoute>
                <StudyPlanner />
              </PrivateRoute>
            } />
            <Route path="/academic-mentor/goals" element={
              <PrivateRoute>
                <StudentGoals />
              </PrivateRoute>
            } />
            <Route path="/parent/academic-insights" element={
              <PrivateRoute>
                <ParentAcademicInsights />
              </PrivateRoute>
            } />
            <Route path="/mentor/students" element={
              <PrivateRoute>
                <MentorStudentDashboard />
              </PrivateRoute>
            } />
            <Route path="/mentor/interventions" element={
              <PrivateRoute>
                <InterventionManager />
              </PrivateRoute>
            } />
            <Route path="/admin/academic-intelligence" element={
              <AdminRoute>
                <AcademicIntelligenceAdmin />
              </AdminRoute>
            } />

            <Route path="/communication-dashboard" element={
              <AdminRoute>
                <CommunicationDashboard />
              </AdminRoute>
            } />

            <Route path="/announcements" element={
              <AdminRoute>
                <AnnouncementManager />
              </AdminRoute>
            } />

            <Route path="/broadcasts" element={
              <AdminRoute>
                <BroadcastManager />
              </AdminRoute>
            } />

            <Route path="/emergency-alerts" element={
              <AdminRoute>
                <EmergencyAlerts />
              </AdminRoute>
            } />

            <Route path="/notification-templates" element={
              <AdminRoute>
                <NotificationTemplates />
              </AdminRoute>
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
