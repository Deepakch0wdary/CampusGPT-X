import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Box, 
  Drawer, 
  AppBar, 
  Toolbar, 
  Typography, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText, 
  IconButton, 
  Divider,
  Button
} from '@mui/material';
import { 
  Menu as MenuIcon, 
  Dashboard as DashboardIcon, 
  PersonAdd as PersonAddIcon, 
  People as PeopleIcon, 
  ExitToApp as ExitIcon,
  School as SchoolIcon
} from '@mui/icons-material';

const DRAWER_WIDTH = 260;

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<any>(null);

  const loadUser = () => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      setUser(JSON.parse(userStr));
    } else {
      setUser(null);
    }
  };

  useEffect(() => {
    loadUser();
    // Re-load on local storage changes
    window.addEventListener('storage', loadUser);
    return () => window.removeEventListener('storage', loadUser);
  }, []);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (e) {
      console.error('Logout request failed:', e);
    } finally {
      localStorage.clear();
      setUser(null);
      navigate('/login');
    }
  };

  const isAuthPage = ['/login', '/forgot-password'].includes(location.pathname);

  // If on login or forgot-password, render content without standard shell
  if (isAuthPage) {
    return (
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', p: 4 }}>
        {children}
      </Box>
    );
  }

  // Dynamic Navigation Items
  const menuItems = [];
  if (user?.role === 'MASTER_ADMIN') {
    menuItems.push(
      { text: 'Overview', icon: <DashboardIcon />, path: '/dashboard' },
      { text: 'Provision User', icon: <PersonAddIcon />, path: '/create-user' },
      { text: 'Directory', icon: <PeopleIcon />, path: '/users' },
      { text: 'Academics', icon: <SchoolIcon />, path: '/academics' }
    );
  } else if (user?.role === 'STUDENT') {
    menuItems.push(
      { text: 'Overview', icon: <DashboardIcon />, path: '/' },
      { text: 'Student Portal', icon: <SchoolIcon />, path: '/student-dashboard' },
      { text: 'Academics', icon: <SchoolIcon />, path: '/academics' }
    );
  } else {
    // Default fallback menu
    menuItems.push(
      { text: 'Overview', icon: <DashboardIcon />, path: '/' },
      { text: 'Academics', icon: <SchoolIcon />, path: '/academics' }
    );
  }

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
      <Box sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 800, color: 'primary.main', fontFamily: 'Outfit' }}>
          CampusGPT <span style={{ color: '#fff' }}>X</span>
        </Typography>
      </Box>
      <Divider />
      <List sx={{ px: 2, py: 3, flexGrow: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
            <ListItemButton 
              onClick={() => {
                navigate(item.path);
                setMobileOpen(false);
              }}
              sx={{ 
                borderRadius: 2,
                bgcolor: location.pathname === item.path ? 'rgba(0, 112, 243, 0.08)' : 'transparent',
                '&:hover': { bgcolor: 'rgba(0, 112, 243, 0.08)' }
              }}
            >
              <ListItemIcon sx={{ color: location.pathname === item.path ? 'primary.main' : 'text.secondary', minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text} 
                primaryTypographyProps={{ fontSize: 14, fontWeight: 500, color: location.pathname === item.path ? 'primary.main' : 'inherit' }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      
      <Divider />
      
      {/* User Card info & Logout */}
      {user && (
        <Box sx={{ p: 2 }}>
          <Box sx={{ mb: 2, px: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }} noWrap>{user.name}</Typography>
            <Typography variant="caption" color="text.secondary" noWrap>{user.email}</Typography>
          </Box>
          <Button 
            variant="outlined" 
            color="error" 
            fullWidth 
            startIcon={<ExitIcon />}
            onClick={handleLogout}
            size="small"
          >
            Log Out
          </Button>
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar 
        position="fixed" 
        sx={{ 
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          bgcolor: 'rgba(2, 6, 23, 0.75)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: 'none',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ fontFamily: 'Outfit', fontWeight: 600, flexGrow: 1 }}>
            Smart Campus Portal
          </Typography>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH, borderRight: '1px solid rgba(255, 255, 255, 0.08)' },
          }}
        >
          {drawerContent}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH, borderRight: '1px solid rgba(255, 255, 255, 0.08)' },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{ 
          flexGrow: 1, 
          p: 4, 
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          mt: '64px',
          minHeight: 'calc(100vh - 64px)',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {children}
      </Box>
    </Box>
  );
};
export default Layout;
