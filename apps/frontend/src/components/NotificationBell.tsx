import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Badge, IconButton, Menu, Typography, Box,
  Divider, Button, List, ListItem, ListItemText, ListItemAvatar, Avatar
} from '@mui/material';
import {
  Notifications as BellIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon
} from '@mui/icons-material';

export const NotificationBell: React.FC = () => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notifications, setNotifications] = useState<any[]>([]);

  const fetchUnread = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      // Count
      const countRes = await fetch('/api/v1/notifications/unread-count', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (countRes.ok) {
        const countData = await countRes.json();
        setUnreadCount(countData.data.unreadCount);
      }

      // Latest 5
      const listRes = await fetch('/api/v1/notifications?unread_only=true&size=5', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (listRes.ok) {
        const listData = await listRes.json();
        setNotifications(listData.data.notifications || []);
      }
    } catch (e) {
      console.error('Failed to load notifications for bell', e);
    }
  };

  useEffect(() => {
    fetchUnread();
    const interval = setInterval(fetchUnread, 15000); // Poll every 15s
    return () => clearInterval(interval);
  }, []);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    fetchUnread();
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleMarkAllRead = async () => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch('/api/v1/notifications/read-all', {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setUnreadCount(0);
      setNotifications([]);
      handleClose();
    } catch (e) {
      console.error(e);
    }
  };

  const handleNotificationClick = async (n: any) => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`/api/v1/notifications/${n.id}/read`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      handleClose();
      fetchUnread();
      if (n.actionUrl) {
        navigate(n.actionUrl);
      } else {
        navigate('/notifications');
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'WARNING': return <WarningIcon color="warning" />;
      case 'ERROR': return <ErrorIcon color="error" />;
      case 'EMERGENCY': return <ErrorIcon color="error" />;
      case 'SUCCESS': return <SuccessIcon color="success" />;
      default: return <InfoIcon color="info" />;
    }
  };

  return (
    <>
      <IconButton color="inherit" onClick={handleClick} id="notification-bell-btn">
        <Badge badgeContent={unreadCount} color="error" max={99}>
          <BellIcon />
        </Badge>
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 360,
            maxHeight: 480,
            bgcolor: 'background.paper',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            boxShadow: '0px 10px 30px rgba(0, 0, 0, 0.5)',
            borderRadius: 2
          }
        }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="subtitle1" fontWeight={700}>Notifications</Typography>
          {unreadCount > 0 && (
            <Button size="small" onClick={handleMarkAllRead} sx={{ fontSize: 12 }}>
              Mark all read
            </Button>
          )}
        </Box>
        <Divider />
        <List sx={{ p: 0 }}>
          {notifications.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">No new notifications</Typography>
            </Box>
          ) : (
            notifications.map((n) => (
              <ListItem
                key={n.id}
                button
                onClick={() => handleNotificationClick(n)}
                sx={{
                  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                  '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.03)' }
                }}
              >
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'transparent' }}>
                    {getIcon(n.type)}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={n.title}
                  secondary={n.body}
                  primaryTypographyProps={{ variant: 'body2', fontWeight: 600, noWrap: true }}
                  secondaryTypographyProps={{ variant: 'caption', noWrap: true }}
                />
              </ListItem>
            ))
          )}
        </List>
        <Divider />
        <Box sx={{ p: 1, textAlign: 'center' }}>
          <Button
            fullWidth
            size="small"
            onClick={() => {
              navigate('/notifications');
              handleClose();
            }}
          >
            View All
          </Button>
        </Box>
      </Menu>
    </>
  );
};
export default NotificationBell;
