import React, { useState, useEffect } from 'react';
import './StabilityView.css';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface Group {
  id: number;
  services: string[];
  data: number[][];
}

interface AvailableOptions {
  dates: string[];
  times: {[date: string]: string[]};
  metric_types: string[];
}

const StabilityView: React.FC = () => {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const [metricType, setMetricType] = useState<string>('CPU');
  const [date, setDate] = useState<string>('');
  const [time, setTime] = useState<string>('');
  const [maxGroupSize, setMaxGroupSize] = useState<number>(3);
  const [stabilityThreshold, setStabilityThreshold] = useState<number>(20);
  
  // Доступні опції для дропдаунів
  const [availableOptions, setAvailableOptions] = useState<AvailableOptions | null>(null);
  const [availableTimes, setAvailableTimes] = useState<string[]>([]);
  const [loadingOptions, setLoadingOptions] = useState<boolean>(false);
  const [loadingGroups, setLoadingGroups] = useState<boolean>(false);
  
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
  
  const fetchGroups = async () => {
    try {
      setLoadingGroups(true);
      setError(null);
      
      // Формування URL із параметрами запиту
      const url = new URL(`${API_BASE_URL}/api/grouping/form-groups`);
      url.searchParams.append('metric_type', metricType);
      url.searchParams.append('date', date);
      url.searchParams.append('time', time);
      url.searchParams.append('max_group_size', maxGroupSize.toString());
      url.searchParams.append('stability_threshold', stabilityThreshold.toString());
      
      // Виконання запиту
      const response = await axios.get(url.toString());
      
      // Заповнення даними для тесту (в реальному застосунку тут буде запит на отримання метрик)
      const groupsWithData = response.data.groups.map((group: any) => ({
        ...group,
        data: group.services.map(() => Array.from({length: 5}, () => Math.floor(Math.random() * 100)))
      }));
      
      setGroups(groupsWithData);
    } catch (err) {
      console.error('Помилка при отриманні груп:', err);
      setError('Не вдалося отримати дані про групи. Спробуйте знову.');
    } finally {
      setLoadingGroups(false);
    }
  };
  
  const fetchStabilityChart = async () => {
    if (groups.length === 0) {
      setError('Спочатку потрібно сформувати групи');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // Підготовка даних для запиту
      const requestData = {
        groups: groups.map(group => group.data),
        group_ids: groups.map(group => group.id)
      };
      
      // Виконання запиту
      const response = await axios.post(
        `${API_BASE_URL}/api/visualization/stability`, 
        requestData,
        { responseType: 'blob' }
      );
      
      // Створення URL для зображення
      const blob = new Blob([response.data], { type: 'image/png' });
      const url = URL.createObjectURL(blob);
      setImageUrl(url);
    } catch (err) {
      console.error('Помилка при отриманні зображення:', err);
      setError('Не вдалося отримати зображення. Спробуйте знову.');
    } finally {
      setLoading(false);
    }
  };
  
  // Вимкнення кнопки при відсутності дати чи часу
  const isFormValid = date && time && metricType;
  
  return (
    <div className="stability-view">
      <h2>Аналіз стабільності груп</h2>
      
      <div className="control-panel">
        {loadingOptions ? (
          <div className="loading-options">Завантаження доступних опцій...</div>
        ) : (
          <div className="form-grid">
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
              <label>Макс. розмір групи:</label>
              <input 
                type="number" 
                min="2" 
                max="10" 
                value={maxGroupSize} 
                onChange={(e) => setMaxGroupSize(parseInt(e.target.value))} 
              />
            </div>
            
            <div className="form-group">
              <label>Поріг стабільності (%):</label>
              <input 
                type="number" 
                min="0" 
                max="100" 
                value={stabilityThreshold} 
                onChange={(e) => setStabilityThreshold(parseInt(e.target.value))} 
              />
            </div>
            
            <button 
              className="fetch-button"
              onClick={fetchGroups}
              disabled={loadingGroups || !isFormValid}
            >
              {loadingGroups ? 'Формування груп...' : 'Сформувати групи'}
            </button>
            
            <button 
              className="fetch-button visualization-button"
              onClick={fetchStabilityChart}
              disabled={loading || groups.length === 0}
            >
              {loading ? 'Завантаження графіка...' : 'Показати графік стабільності'}
            </button>
          </div>
        )}
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {groups.length > 0 && (
        <div className="groups-summary">
          <h3>Сформовані групи:</h3>
          <div className="groups-list">
            {groups.map((group) => (
              <div key={group.id} className="group-summary-item">
                <h4>Група {group.id}</h4>
                <p>{group.services.length} сервісів</p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="chart-container">
        {loading ? (
          <div className="loading">Завантаження графіка...</div>
        ) : imageUrl ? (
          <img 
            src={imageUrl} 
            alt="Графік стабільності груп" 
            className="stability-chart" 
          />
        ) : (
          <div className="placeholder">
            {groups.length === 0 
              ? 'Спочатку сформуйте групи, а потім натисніть кнопку для відображення графіка стабільності'
              : 'Натисніть кнопку для відображення графіка стабільності'}
          </div>
        )}
      </div>
    </div>
  );
};

export default StabilityView; 