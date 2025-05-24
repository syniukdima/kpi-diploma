import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box
} from '@mui/material';

const Navigation: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string): boolean => {
    return location.pathname === path;
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 0, mr: 4 }}>
          Microservices
        </Typography>
        <Box sx={{ flexGrow: 1, display: 'flex', gap: 2 }}>
          <Button
            color="inherit"
            component={Link}
            to="/normalization"
            variant={isActive('/normalization') ? 'outlined' : 'text'}
          >
            Нормалізація
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/autonormalization"
            variant={isActive('/autonormalization') ? 'outlined' : 'text'}
          >
            Автонормалізація
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/grouping"
            variant={isActive('/grouping') ? 'outlined' : 'text'}
          >
            Групування
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/visualization"
            variant={isActive('/visualization') ? 'outlined' : 'text'}
          >
            Візуалізація
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation; 