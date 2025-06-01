import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select';

const API_BASE_URL = 'https://syniukdmytro.online';

interface ResourceInfo {
  name: string;
  standard_value: string;
  usage_percentage: number;
}

interface AutoNormalizationResult {
  resources: ResourceInfo[];
  key_resource: string;
}

const AutoNormalization: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedTime, setSelectedTime] = useState<string>('');
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [availableTimes, setAvailableTimes] = useState<string[]>([]);
  const [result, setResult] = useState<AutoNormalizationResult | null>(null);
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchDates();
  }, []);

  useEffect(() => {
    if (selectedDate) {
      fetchTimes();
    }
  }, [selectedDate]);

  const fetchDates = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/metrics/raw-data-options`);
      const data = await response.json();
      setAvailableDates(data.dates);
      setSelectedDate('');
      setSelectedTime('');
    } catch (err) {
      setError('Помилка при отриманні доступних дат');
    }
  };

  const fetchTimes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/metrics/raw-data-options`);
      const data = await response.json();
      if (data.times && data.times[selectedDate]) {
        setAvailableTimes(data.times[selectedDate]);
      } else {
        setAvailableTimes([]);
      }
      setSelectedTime('');
    } catch (err) {
      setError('Помилка при отриманні доступних часів');
    }
  };

  const handleDateChange = (event: SelectChangeEvent) => {
    setSelectedDate(event.target.value);
    setResult(null);
  };

  const handleTimeChange = (event: SelectChangeEvent) => {
    setSelectedTime(event.target.value);
    setResult(null);
  };

  const handleNormalize = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/autonormalization/analyze-and-normalize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          date: selectedDate,
          time: selectedTime,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Помилка при нормалізації даних');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка при виконанні автонормалізації');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Автоматична нормалізація
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Дата</InputLabel>
              <Select
                value={selectedDate}
                label="Дата"
                onChange={handleDateChange}
              >
                {availableDates.map((date) => (
                  <MenuItem key={date} value={date}>
                    {date}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Час</InputLabel>
              <Select
                value={selectedTime}
                label="Час"
                onChange={handleTimeChange}
                disabled={!selectedDate}
              >
                {availableTimes.map((time) => (
                  <MenuItem key={time} value={time}>
                    {time}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <Box sx={{ mt: 3 }}>
          <Button
            variant="contained"
            onClick={handleNormalize}
            disabled={!selectedDate || !selectedTime || isLoading}
            fullWidth
          >
            {isLoading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              'Виконати автонормалізацію'
            )}
          </Button>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Результат аналізу
          </Typography>
          
          <TableContainer sx={{ mb: 3 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Критерій</TableCell>
                  <TableCell>Стандартне значення</TableCell>
                  <TableCell>Максимальний відсоток використання</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {result.resources.map((resource) => (
                  <TableRow key={resource.name}>
                    <TableCell>{resource.name}</TableCell>
                    <TableCell>{resource.standard_value}</TableCell>
                    <TableCell>{resource.usage_percentage}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="body2" color="text.secondary">
            Нормалізацію проведено за показником: {result.key_resource}
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default AutoNormalization; 