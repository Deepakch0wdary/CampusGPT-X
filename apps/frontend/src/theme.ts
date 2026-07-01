import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#0070f3', // Brand accent Blue
      light: '#e0effe',
      dark: '#0060d9',
    },
    secondary: {
      main: '#f43f5e', // Rose accent
    },
    background: {
      default: '#020617', // Slate 950
      paper: '#0f172a',   // Slate 900
    },
    text: {
      primary: '#f8fafc',
      secondary: '#94a3b8',
    },
    divider: 'rgba(255, 255, 255, 0.08)',
  },
  typography: {
    fontFamily: [
      'Inter',
      'Outfit',
      'sans-serif',
    ].join(','),
    h1: {
      fontWeight: 800,
      fontFamily: 'Outfit, sans-serif',
    },
    h2: {
      fontWeight: 700,
      fontFamily: 'Outfit, sans-serif',
    },
    h5: {
      fontWeight: 600,
      fontFamily: 'Outfit, sans-serif',
    },
    body1: {
      lineHeight: 1.6,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      letterSpacing: '0.02em',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderRadius: 12,
          border: '1px solid rgba(255, 255, 255, 0.08)',
        },
      },
    },
  },
});
export default theme;
