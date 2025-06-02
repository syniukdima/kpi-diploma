import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid
} from '@mui/material';
import '../components/MobileStyles.css';
import { API_BASE_URL } from '../config/api.ts';

interface RawMetric {
  service_name: string;
  metric_type: string;
  date: string;
  time: string;
  values: number[];
}

const RawMetricsView: React.FC = () => {
  const [metrics, setMetrics] = useState<RawMetric[]>([]);
  const [allMetrics, setAllMetrics] = useState<RawMetric[]>([]);
  const [error, setError] = useState<string>('');
  const [filters, setFilters] = useState({
    metric_type: '',
    service_name: '',
    date: '',
    time: ''
  });

  // Отримуємо унікальні значення для фільтрів з повного списку метрик
  const uniqueServices = [...new Set(allMetrics.map(m => m.service_name))].sort();
  const metricTypes = ['CPU', 'RAM', 'CHANNEL'];
  const uniqueDates = [...new Set(allMetrics.map(m => m.date))].sort();
  const uniqueTimes = [...new Set(allMetrics.map(m => m.time))].sort();

  const fetchMetrics = async () => {
    try {
      // Будуємо URL з фільтрами
      const params = new URLSearchParams();
      if (filters.metric_type) params.append('metric_type', filters.metric_type);
      if (filters.service_name) params.append('service_name', filters.service_name);
      if (filters.date) params.append('date', filters.date);
      if (filters.time) params.append('time', filters.time);

      const response = await fetch(`${API_BASE_URL}/api/metrics/raw-data?${params.toString()}`);
      if (!response.ok) {
        throw new Error('Помилка при отриманні даних');
      }
      const data = await response.json();
      setMetrics(data);

      // Зберігаємо повний список метрик при першому завантаженні
      if (!filters.metric_type && !filters.service_name && !filters.date && !filters.time) {
        setAllMetrics(data);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, [filters]);

  const handleFilterChange = (field: string) => (event: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box className="raw-metrics-container">
      <Typography variant="h4" component="h1" gutterBottom>
        Сирі метрики
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            label="Пошук за назвою сервісу"
            value={filters.service_name}
            onChange={handleFilterChange('service_name')}
            variant="outlined"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth>
            <InputLabel>Тип метрики</InputLabel>
            <Select
              value={filters.metric_type}
              onChange={handleFilterChange('metric_type')}
              label="Тип метрики"
            >
              <MenuItem value="">Всі</MenuItem>
              {metricTypes.map(type => (
                <MenuItem key={type} value={type}>{type}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth>
            <InputLabel>Дата</InputLabel>
            <Select
              value={filters.date}
              onChange={handleFilterChange('date')}
              label="Дата"
            >
              <MenuItem value="">Всі</MenuItem>
              {uniqueDates.map(date => (
                <MenuItem key={date} value={date}>{date}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth>
            <InputLabel>Час</InputLabel>
            <Select
              value={filters.time}
              onChange={handleFilterChange('time')}
              label="Час"
            >
              <MenuItem value="">Всі</MenuItem>
              {uniqueTimes.map(time => (
                <MenuItem key={time} value={time}>{time}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Сервіс</TableCell>
              <TableCell>Тип метрики</TableCell>
              <TableCell>Дата</TableCell>
              <TableCell>Час</TableCell>
              <TableCell>Значення</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {metrics.map((metric, index) => (
              <TableRow key={`${metric.service_name}-${metric.date}-${metric.time}-${index}`}>
                <TableCell>{metric.service_name}</TableCell>
                <TableCell>{metric.metric_type}</TableCell>
                <TableCell>{metric.date}</TableCell>
                <TableCell>{metric.time}</TableCell>
                <TableCell>{metric.values.map(v => v.toFixed(2)).join(', ')}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default RawMetricsView; 