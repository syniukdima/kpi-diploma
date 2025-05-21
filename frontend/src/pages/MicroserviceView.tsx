import React, { useState, useEffect } from 'react';
import './MicroserviceView.css';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface MetricData {
  x: number;
  y: number;
}

interface Series {
  name: string;
  data: MetricData[];
}

interface ChartData {
  series: Series[];
  title: string;
  xlabel: string;
  ylabel: string;
}

interface AvailableOptions {
  dates: string[];
  times: {[date: string]: string[]};
  metric_types: string[];
}

const MicroserviceView: React.FC = () => {
  const [metricType, setMetricType] = useState<string>('CPU');
  const [date, setDate] = useState<string>('');
  const [time, setTime] = useState<string>('');
  const [normalizationType, setNormalizationType] = useState<string | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Доступні опції для дропдаунів
  const [availableOptions, setAvailableOptions] = useState<AvailableOptions | null>(null);
  const [availableTimes, setAvailableTimes] = useState<string[]>([]);
  const [loadingOptions, setLoadingOptions] = useState<boolean>(false);
  
  // Завантаження доступних опцій при першому рендері
  useEffect(() => {
    const fetchAvailableOptions = async () => {
      try {
        setLoadingOptions(true);
        const response = await axios.get(`${API_BASE_URL}/api/metrics/available-options`);
        setAvailableOptions(response.data);
        
        // Встановлення початкових значень
        if (response.data.dates.length > 0) {
          setDate(response.data.dates[0]);
          
          // Встановлення доступних часів для вибраної дати
          if (response.data.times[response.data.dates[0]].length > 0) {
            setAvailableTimes(response.data.times[response.data.dates[0]]);
            setTime(response.data.times[response.data.dates[0]][0]);
          }
        }
        
        if (response.data.metric_types.length > 0) {
          setMetricType(response.data.metric_types[0]);
        }
      } catch (err) {
        console.error('Помилка при отриманні доступних опцій:', err);
        setError('Не вдалося завантажити доступні опції. Спробуйте оновити сторінку.');
      } finally {
        setLoadingOptions(false);
      }
    };
    
    fetchAvailableOptions();
  }, []);
  
  // Оновлення доступних часів при зміні дати
  useEffect(() => {
    if (availableOptions && date) {
      setAvailableTimes(availableOptions.times[date] || []);
      if (availableOptions.times[date] && availableOptions.times[date].length > 0) {
        setTime(availableOptions.times[date][0]);
      } else {
        setTime('');
      }
    }
  }, [date, availableOptions]);
  
  const fetchMicroserviceData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Формування URL із параметрами запиту
      const url = new URL(`${API_BASE_URL}/api/visualization/microservices`);
      url.searchParams.append('metric_type', metricType);
      url.searchParams.append('date', date);
      url.searchParams.append('time', time);
      if (normalizationType) {
        url.searchParams.append('normalization_type', normalizationType);
      }
      
      // Виконання запиту
      const response = await axios.get(url.toString());
      setChartData(response.data);
    } catch (err) {
      console.error('Помилка при отриманні даних:', err);
      setError('Не вдалося отримати дані. Спробуйте знову.');
    } finally {
      setLoading(false);
    }
  };
  
  const renderChart = () => {
    if (!chartData) return null;
    
    return (
      <div className="chart-rendered">
        <h3>{chartData.title}</h3>
        <div className="chart-placeholder">
          {chartData.series.map((series, index) => (
            <div key={index} className="series-item">
              <div 
                className="series-color" 
                style={{ backgroundColor: getColorForIndex(index) }} 
              />
              <div className="series-name">{series.name}</div>
            </div>
          ))}
        </div>
        <div className="chart-info">
          <p className="chart-axis-label">
            {chartData.xlabel}: горизонтальна вісь
          </p>
          <p className="chart-axis-label">
            {chartData.ylabel}: вертикальна вісь
          </p>
        </div>
      </div>
    );
  };
  
  // Допоміжна функція для отримання кольору за індексом
  const getColorForIndex = (index: number): string => {
    const colors = [
      '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
      '#1abc9c', '#d35400', '#34495e', '#7f8c8d', '#c0392b'
    ];
    return colors[index % colors.length];
  };
  
  // Вимкнення кнопки при відсутності дати чи часу
  const isFormValid = date && time && metricType;
  
  return (
    <div className="microservice-view">
      <h2>Аналіз мікросервісів</h2>
      
      <div className="control-panel">
        {loadingOptions ? (
          <div className="loading-options">Завантаження доступних опцій...</div>
        ) : (
          <>
            <div className="form-group">
              <label>Тип метрики:</label>
              <select 
                value={metricType} 
                onChange={(e) => setMetricType(e.target.value)}
              >
                {availableOptions?.metric_types.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Дата:</label>
              <select 
                value={date} 
                onChange={(e) => setDate(e.target.value)} 
              >
                {availableOptions?.dates.map(date => (
                  <option key={date} value={date}>{date}</option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Час:</label>
              <select 
                value={time} 
                onChange={(e) => setTime(e.target.value)}
                disabled={availableTimes.length === 0}
              >
                {availableTimes.map(time => (
                  <option key={time} value={time}>{time}</option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Нормалізація:</label>
              <select 
                value={normalizationType || ''} 
                onChange={(e) => setNormalizationType(e.target.value || null)}
              >
                <option value="">Без нормалізації</option>
                <option value="min_max">Min-Max</option>
                <option value="z_score">Z-Score</option>
              </select>
            </div>
            
            <button 
              className="fetch-button"
              onClick={fetchMicroserviceData}
              disabled={loading || !isFormValid}
            >
              {loading ? 'Завантаження...' : 'Отримати дані'}
            </button>
          </>
        )}
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="chart-container">
        {loading ? (
          <div className="loading">Завантаження даних...</div>
        ) : chartData ? (
          renderChart()
        ) : (
          <div className="placeholder">
            Налаштуйте параметри та натисніть кнопку для відображення даних
          </div>
        )}
      </div>
    </div>
  );
};

export default MicroserviceView; 