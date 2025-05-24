import React, { useState, useEffect } from 'react';
import './GroupingView.css';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface MicroserviceGroup {
  group_number: number;
  services: string[];
  values: number[];
}

interface AvailableOptions {
  dates: string[];
  times: {[date: string]: string[]};
  metric_types: string[];
}

interface GroupStatistics {
  group_id: number;
  num_services: number;
  mean_load: number;
  peak_load: number;
  stability: number;
  services: string[];
}

interface TimeSeriesPoint {
  x: number;
  y: number;
}

interface TimeSeriesData {
  name: string;
  data: TimeSeriesPoint[];
}

type VisualizationType = 'load' | 'stability' | 'statistics' | 'distribution' | 'microservices' | 'base-peak';

const GroupingView: React.FC = () => {
  const [metricType, setMetricType] = useState<string>('CPU');
  const [date, setDate] = useState<string>('');
  const [time, setTime] = useState<string>('');
  const [maxGroupSize, setMaxGroupSize] = useState<number>(4);
  const [stabilityThreshold, setStabilityThreshold] = useState<number>(20);
  const [groups, setGroups] = useState<number[]>([]);
  const [groupDetails, setGroupDetails] = useState<MicroserviceGroup[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);
  const [splitData, setSplitData] = useState<any>(null);
  const [loadingSplit, setLoadingSplit] = useState<boolean>(false);
  
  // Доступні опції для дропдаунів
  const [availableOptions, setAvailableOptions] = useState<AvailableOptions | null>(null);
  const [availableTimes, setAvailableTimes] = useState<string[]>([]);
  const [loadingOptions, setLoadingOptions] = useState<boolean>(false);
  
  // Стан для візуалізацій
  const [visualization, setVisualization] = useState<VisualizationType>('load');
  const [loadChartUrl, setLoadChartUrl] = useState<string | null>(null);
  const [loadingLoadChart, setLoadingLoadChart] = useState<boolean>(false);
  const [stabilityChartUrl, setStabilityChartUrl] = useState<string | null>(null);
  const [loadingStabilityChart, setLoadingStabilityChart] = useState<boolean>(false);
  const [groupStatistics, setGroupStatistics] = useState<GroupStatistics[]>([]);
  const [loadingStatistics, setLoadingStatistics] = useState<boolean>(false);
  const [distributionChartUrl, setDistributionChartUrl] = useState<string | null>(null);
  const [loadingDistributionChart, setLoadingDistributionChart] = useState<boolean>(false);
  
  // Стан для мікросервісів
  const [loadingMicroservices, setLoadingMicroservices] = useState<boolean>(false);
  const [microservicesChartUrl, setMicroservicesChartUrl] = useState<string | null>(null);
  
  // Стан для базово-пікових компонентів
  const [selectedServiceForBasePeak, setSelectedServiceForBasePeak] = useState<string | null>(null);
  const [loadingBasePeak, setLoadingBasePeak] = useState<boolean>(false);
  const [basePeakChartUrl, setBasePeakChartUrl] = useState<string | null>(null);
  const [splitServices, setSplitServices] = useState<string[]>([]);
  
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
      setLoading(true);
      setError(null);
      
      // Скидання попередніх результатів
      setSelectedGroup(null);
      setSplitData(null);
      setLoadChartUrl(null);
      setStabilityChartUrl(null);
      setGroupStatistics([]);
      setDistributionChartUrl(null);
      setMicroservicesChartUrl(null);
      setBasePeakChartUrl(null);
      setSplitServices([]);
      
      // Формування URL із параметрами запиту
      const url = new URL(`${API_BASE_URL}/api/grouping/form-groups`);
      url.searchParams.append('metric_type', metricType);
      url.searchParams.append('date', date);
      url.searchParams.append('time', time);
      url.searchParams.append('max_group_size', maxGroupSize.toString());
      url.searchParams.append('stability_threshold', stabilityThreshold.toString());
      
      // Виконання запиту
      const response = await axios.get(url.toString());
      
      // Логування відповіді
      console.log('Response data:', response.data);
      console.log('Groups from response:', response.data.groups);
      
      // Обробка відповіді
      const groupData = response.data.groups;
      console.log('Group data before mapping:', groupData);
      
      // Перевірка структури даних та коректне мапування
      const groupIds = groupData.map((g: any) => {
        console.log('Processing group:', g);
        return typeof g === 'object' ? g.group_number : g;
      });
      
      console.log('Mapped group IDs:', groupIds);
      
      setGroupDetails(groupData);
      setGroups(groupIds);
      
      // Автоматично завантажити дані для початкової вкладки
      if (groupData.length > 0) {
        setVisualization('load');
        fetchGroupLoadData();
      }
    } catch (err) {
      console.error('Помилка при отриманні груп:', err);
      setError('Не вдалося отримати дані про групи. Спробуйте знову.');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchSplitData = async (serviceName: string) => {
    try {
      setLoadingSplit(true);
      
      // Формування URL із параметрами запиту
      const url = new URL(`${API_BASE_URL}/api/visualization/split/${encodeURIComponent(serviceName)}`);
      url.searchParams.append('metric_type', metricType);
      url.searchParams.append('date', date);
      url.searchParams.append('time', time);
      
      // Виконання запиту
      const response = await axios.get(url.toString());
      
      // Обробка відповіді
      setSplitData(response.data);
    } catch (err) {
      console.error('Помилка при отриманні даних про розділення:', err);
    } finally {
      setLoadingSplit(false);
    }
  };
  
  // Отримання даних для графіку навантаження груп
  const fetchGroupLoadData = async () => {
    try {
      setLoadingLoadChart(true);
      
      // Формування URL із параметрами запиту
      const requestUrl = new URL(`${API_BASE_URL}/api/visualization/group-load`);
      requestUrl.searchParams.append('metric_type', metricType);
      requestUrl.searchParams.append('date', date);
      requestUrl.searchParams.append('time', time);
      requestUrl.searchParams.append('max_group_size', maxGroupSize.toString());
      requestUrl.searchParams.append('stability_threshold', stabilityThreshold.toString());
      
      // Виконання запиту
      const response = await axios.get(requestUrl.toString(), { responseType: 'blob' });
      
      // Створення URL для зображення
      const blob = new Blob([response.data], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);
      setLoadChartUrl(imageUrl);
    } catch (err) {
      console.error('Помилка при отриманні графіку навантаження груп:', err);
    } finally {
      setLoadingLoadChart(false);
    }
  };
  
  // Отримання графіку стабільності груп
  const fetchStabilityChart = async () => {
    try {
      setLoadingStabilityChart(true);
      
      // Формування URL із параметрами запиту
      const requestUrl = new URL(`${API_BASE_URL}/api/visualization/stability-direct`);
      requestUrl.searchParams.append('metric_type', metricType);
      requestUrl.searchParams.append('date', date);
      requestUrl.searchParams.append('time', time);
      requestUrl.searchParams.append('max_group_size', maxGroupSize.toString());
      requestUrl.searchParams.append('stability_threshold', stabilityThreshold.toString());
      
      // Виконання запиту
      const response = await axios.get(requestUrl.toString(), { responseType: 'blob' });
      
      // Створення URL для зображення
      const blob = new Blob([response.data], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);
      setStabilityChartUrl(imageUrl);
    } catch (err) {
      console.error('Помилка при отриманні графіку стабільності:', err);
    } finally {
      setLoadingStabilityChart(false);
    }
  };
  
  // Отримання статистики груп
  const fetchGroupStatistics = async () => {
    try {
      setLoadingStatistics(true);
      
      // Формування URL із параметрами запиту
      const url = new URL(`${API_BASE_URL}/api/visualization/group-statistics`);
      url.searchParams.append('metric_type', metricType);
      url.searchParams.append('date', date);
      url.searchParams.append('time', time);
      url.searchParams.append('max_group_size', maxGroupSize.toString());
      url.searchParams.append('stability_threshold', stabilityThreshold.toString());
      
      // Виконання запиту
      const response = await axios.get(url.toString());
      
      // Обробка відповіді
      setGroupStatistics(response.data.statistics);
    } catch (err) {
      console.error('Помилка при отриманні статистики груп:', err);
    } finally {
      setLoadingStatistics(false);
    }
  };
  
  // Отримання графіку розподілу навантаження
  const fetchDistributionChart = async (groupId: number) => {
    try {
      setLoadingDistributionChart(true);
      
      // Формування URL із параметрами запиту
      const url = new URL(`${API_BASE_URL}/api/visualization/group-load-distribution`);
      url.searchParams.append('group_id', groupId.toString());
      url.searchParams.append('metric_type', metricType);
      url.searchParams.append('date', date);
      url.searchParams.append('time', time);
      url.searchParams.append('max_group_size', maxGroupSize.toString());
      url.searchParams.append('stability_threshold', stabilityThreshold.toString());
      
      // Виконання запиту
      const response = await axios.get(url.toString(), { responseType: 'blob' });
      
      // Створення URL для зображення
      const blob = new Blob([response.data], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);
      setDistributionChartUrl(imageUrl);
    } catch (err) {
      console.error('Помилка при отриманні графіку розподілу навантаження:', err);
    } finally {
      setLoadingDistributionChart(false);
    }
  };
  
  // Отримання даних про мікросервіси і їх графіку
  const fetchMicroservicesData = async () => {
    try {
      setLoadingMicroservices(true);
      
      // Отримання графіку мікросервісів
      const chartUrl = new URL(`${API_BASE_URL}/api/visualization/microservices-chart`);
      chartUrl.searchParams.append('metric_type', metricType);
      chartUrl.searchParams.append('date', date);
      chartUrl.searchParams.append('time', time);
      
      const chartResponse = await axios.get(chartUrl.toString(), { responseType: 'blob' });
      
      // Створення URL для зображення
      const blob = new Blob([chartResponse.data], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);
      setMicroservicesChartUrl(imageUrl);
      
    } catch (err) {
      console.error('Помилка при отриманні даних про мікросервіси:', err);
    } finally {
      setLoadingMicroservices(false);
    }
  };
  
  // Отримання даних про базово-пікові компоненти
  const fetchBasePeakData = async () => {
    try {
      setLoadingBasePeak(true);
      
      // Спочатку знаходимо, які мікросервіси були розділені на базові та пікові компоненти
      const findSplitServicesUrl = new URL(`${API_BASE_URL}/api/grouping/find-split-services`);
      findSplitServicesUrl.searchParams.append('metric_type', metricType);
      findSplitServicesUrl.searchParams.append('date', date);
      findSplitServicesUrl.searchParams.append('time', time);
      findSplitServicesUrl.searchParams.append('max_group_size', maxGroupSize.toString());
      findSplitServicesUrl.searchParams.append('stability_threshold', stabilityThreshold.toString());
      
      const splitResponse = await axios.get(findSplitServicesUrl.toString());
      
      const foundSplitServices = splitResponse.data.split_services || [];
      setSplitServices(foundSplitServices);
      
      // Якщо є розділені мікросервіси, вибираємо перший і отримуємо для нього графік
      if (foundSplitServices.length > 0) {
        setSelectedServiceForBasePeak(foundSplitServices[0]);
        await fetchBasePeakChart(foundSplitServices[0]);
      }
    } catch (err) {
      console.error('Помилка при отриманні даних про базово-пікові компоненти:', err);
    } finally {
      setLoadingBasePeak(false);
    }
  };
  
  // Отримання графіку розділення на базовий та піковий компоненти
  const fetchBasePeakChart = async (serviceName: string) => {
    try {
      setLoadingBasePeak(true);
      
      // Формування URL із параметрами запиту
      const chartUrl = new URL(`${API_BASE_URL}/api/visualization/base-peak-component`);
      chartUrl.searchParams.append('service_name', serviceName);
      chartUrl.searchParams.append('metric_type', metricType);
      chartUrl.searchParams.append('date', date);
      chartUrl.searchParams.append('time', time);
      
      const chartResponse = await axios.get(chartUrl.toString(), { responseType: 'blob' });
      
      // Створення URL для зображення
      const blob = new Blob([chartResponse.data], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);
      setBasePeakChartUrl(imageUrl);
    } catch (err) {
      console.error('Помилка при отриманні графіку базово-пікових компонентів:', err);
    } finally {
      setLoadingBasePeak(false);
    }
  };
  
  // Перемикання візуалізації та завантаження відповідних даних
  const switchVisualization = (visType: VisualizationType) => {
    setVisualization(visType);
    
    // Завантаження даних при зміні вкладки
    switch (visType) {
      case 'load':
        if (!loadChartUrl) fetchGroupLoadData();
        break;
      case 'stability':
        if (!stabilityChartUrl) fetchStabilityChart();
        break;
      case 'statistics':
        if (groupStatistics.length === 0) fetchGroupStatistics();
        break;
      case 'microservices':
        if (!microservicesChartUrl) fetchMicroservicesData();
        break;
      case 'base-peak':
        if (splitServices.length === 0) fetchBasePeakData();
        break;
    }
    
    // Якщо вибрана група і відкрита вкладка distribution
    if (selectedGroup !== null && visType === 'distribution') {
      fetchDistributionChart(selectedGroup);
      console.log(selectedGroup);
    }
  };
  
  // Вимкнення кнопки при відсутності дати чи часу
  const isFormValid = date && time && metricType;
  
  // Рендерінг візуалізацій
  const renderVisualization = () => {
    switch (visualization) {
      case 'load':
        return (
          <div className="load-chart">
            {loadingLoadChart ? (
              <div className="loading">Завантаження графіку навантаження груп...</div>
            ) : loadChartUrl ? (
              <div className="chart-image">
                <img 
                  src={loadChartUrl} 
                  alt="Графік навантаження груп" 
                  className="load-chart-img" 
                />
              </div>
            ) : (
              <div className="placeholder">
                <button 
                  className="fetch-button"
                  onClick={fetchGroupLoadData}
                  disabled={loading || groups.length === 0}
                >
                  Завантажити графік навантаження груп
                </button>
              </div>
            )}
          </div>
        );
      
      case 'stability':
        return (
          <div className="stability-chart-container">
            {loadingStabilityChart ? (
              <div className="loading">Завантаження графіку стабільності груп...</div>
            ) : stabilityChartUrl ? (
              <div className="chart-image">
                <img 
                  src={stabilityChartUrl} 
                  alt="Графік стабільності груп" 
                  className="stability-chart" 
                />
              </div>
            ) : (
              <div className="placeholder">
                <button 
                  className="fetch-button"
                  onClick={fetchStabilityChart}
                  disabled={loading || groups.length === 0}
                >
                  Завантажити графік стабільності
                </button>
              </div>
            )}
          </div>
        );
      
      case 'statistics':
        return (
          <div className="statistics-container">
            {loadingStatistics ? (
              <div className="loading">Завантаження статистики груп...</div>
            ) : groupStatistics.length > 0 ? (
              <div className="statistics-content">
                {groupStatistics.map(stats => (
                  <div key={stats.group_id} className="group-statistics">
                    <h3>Група {stats.group_id}</h3>
                    <ul className="stats-list">
                      <li><strong>Кількість мікросервісів:</strong> {stats.num_services}</li>
                      <li><strong>Середнє навантаження:</strong> {stats.mean_load.toFixed(2)}</li>
                      <li><strong>Пікове навантаження:</strong> {stats.peak_load.toFixed(2)}</li>
                      <li><strong>Коефіцієнт стабільності (%):</strong> {stats.stability.toFixed(2)}</li>
                    </ul>
                    <h4>Мікросервіси:</h4>
                    <ul className="services-list-simple">
                      {stats.services.map((service, idx) => (
                        <li key={idx}>{service}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            ) : (
              <div className="placeholder">
                <button 
                  className="fetch-button"
                  onClick={fetchGroupStatistics}
                  disabled={loading || groups.length === 0}
                >
                  Завантажити статистику груп
                </button>
              </div>
            )}
          </div>
        );
      
      case 'distribution':
        return (
          <div className="distribution-chart-container">
            <div className="group-selector">
              <label htmlFor="group-select">Виберіть групу: </label>
              <select 
                id="group-select"
                value={selectedGroup || ''}
                onChange={(e) => {
                  // Перевіряємо, що значення не пусте
                  if (e.target.value) {
                    const groupId = parseInt(e.target.value);
                    // Перевіряємо, що значення успішно конвертовано в число
                    if (!isNaN(groupId)) {
                      setSelectedGroup(groupId);
                      setDistributionChartUrl(null);
                      fetchDistributionChart(groupId);
                    }
                  } else {
                    setSelectedGroup(null);
                    setDistributionChartUrl(null);
                  }
                }}
              >
                <option value="">Оберіть групу</option>
                {groups.map(groupId => {
                  const groupInfo = groupDetails.find(g => g.group_number === groupId);
                  return (
                    <option key={groupId} value={groupId}>
                      Група {groupId} {groupInfo ? `(${groupInfo.services.length} сервісів)` : ''}
                    </option>
                  );
                })}
              </select>
            </div>
            
            {!selectedGroup ? (
              <div className="placeholder">
                Виберіть групу для відображення розподілу навантаження
              </div>
            ) : loadingDistributionChart ? (
              <div className="loading">Завантаження графіку розподілу навантаження...</div>
            ) : distributionChartUrl ? (
              <div className="chart-image">
                <img 
                  src={distributionChartUrl} 
                  alt={`Розподіл навантаження в групі ${selectedGroup}`} 
                  className="distribution-chart" 
                />
              </div>
            ) : (
              <div className="placeholder">
                <button 
                  className="fetch-button"
                  onClick={() => {
                    if (selectedGroup !== null && !isNaN(selectedGroup)) {
                      fetchDistributionChart(selectedGroup);
                    }
                  }}
                  disabled={loading || !selectedGroup || isNaN(selectedGroup)}
                >
                  Завантажити графік розподілу навантаження
                </button>
              </div>
            )}
          </div>
        );
      
      case 'microservices':
        return (
          <div className="microservices-container">
            {loadingMicroservices ? (
              <div className="loading">Завантаження даних про мікросервіси...</div>
            ) : (
              <div className="microservices-chart">
                {microservicesChartUrl ? (
                  <div className="chart-image">
                    <img 
                      src={microservicesChartUrl} 
                      alt="Часові ряди мікросервісів" 
                      className="microservices-chart-img" 
                    />
                  </div>
                ) : (
                  <div className="placeholder">
                    <button 
                      className="fetch-button"
                      onClick={fetchMicroservicesData}
                      disabled={loading || groups.length === 0}
                    >
                      Завантажити графік мікросервісів
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      
      case 'base-peak':
        return (
          <div className="base-peak-container">
            {loadingBasePeak ? (
              <div className="loading">Завантаження даних про базово-пікові компоненти...</div>
            ) : splitServices.length === 0 ? (
              <div className="placeholder">
                Немає мікросервісів, які були розділені на базові та пікові компоненти
              </div>
            ) : (
              <>
                <div className="service-selector">
                  <label htmlFor="service-select">Виберіть мікросервіс: </label>
                  <select 
                    id="service-select"
                    value={selectedServiceForBasePeak || ''}
                    onChange={(e) => {
                      const serviceName = e.target.value;
                      setSelectedServiceForBasePeak(serviceName);
                      fetchBasePeakChart(serviceName);
                    }}
                  >
                    {splitServices.map(service => (
                      <option key={service} value={service}>{service}</option>
                    ))}
                  </select>
                </div>
                
                {basePeakChartUrl ? (
                  <div className="chart-image">
                    <img 
                      src={basePeakChartUrl} 
                      alt="Графік базово-пікового компоненту" 
                      className="base-peak-chart" 
                    />
                  </div>
                ) : (
                  <div className="placeholder">
                    <button 
                      className="fetch-button"
                      onClick={() => selectedServiceForBasePeak && fetchBasePeakChart(selectedServiceForBasePeak)}
                      disabled={!selectedServiceForBasePeak}
                    >
                      Завантажити графік базово-пікового компоненту
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        );
      
      default:
        return null;
    }
  };
  
  return (
    <div className="grouping-view">
      <h2>Групування мікросервісів</h2>
      
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
                disabled={loading || loadingOptions}
              >
                {availableOptions?.metric_types.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Дата:</label>
              <select 
                value={date}
                onChange={(e) => setDate(e.target.value)}
                disabled={loading || loadingOptions || !availableOptions?.dates.length}
              >
                {availableOptions?.dates.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Час:</label>
              <select 
                value={time}
                onChange={(e) => setTime(e.target.value)}
                disabled={loading || loadingOptions || !availableTimes.length}
              >
                {availableTimes.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div className="numeric-input">
              <label>Макс. розмір групи:</label>
              <input 
                type="number"
                value={maxGroupSize}
                onChange={(e) => setMaxGroupSize(Math.max(1, parseInt(e.target.value) || 1))}
                min="1"
                disabled={loading}
              />
            </div>
            <div className="numeric-input">
              <label>Поріг стабільності (%):</label>
              <input 
                type="number"
                value={stabilityThreshold}
                onChange={(e) => setStabilityThreshold(Math.max(0, parseInt(e.target.value) || 0))}
                min="0"
                max="100"
                disabled={loading}
              />
            </div>
          </div>
        )}
        
        <button 
          className="fetch-button"
          onClick={fetchGroups}
          disabled={loading || !isFormValid}
        >
          {loading ? 'Формування груп...' : 'Сформувати групи'}
        </button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {groups.length > 0 && (
        <>
          <div className="visualization-tabs">
            <button 
              className={`tab-button ${visualization === 'load' ? 'active' : ''}`} 
              onClick={() => switchVisualization('load')}
            >
              Навантаження груп
            </button>
            <button 
              className={`tab-button ${visualization === 'stability' ? 'active' : ''}`}
              onClick={() => switchVisualization('stability')}
            >
              Стабільність
            </button>
            <button 
              className={`tab-button ${visualization === 'statistics' ? 'active' : ''}`}
              onClick={() => switchVisualization('statistics')}
            >
              Статистика
            </button>
            <button 
              className={`tab-button ${visualization === 'distribution' ? 'active' : ''}`}
              onClick={() => switchVisualization('distribution')}
            >
              Розподіл навантаження
            </button>
            <button 
              className={`tab-button ${visualization === 'microservices' ? 'active' : ''}`}
              onClick={() => switchVisualization('microservices')}
            >
              Мікросервіси
            </button>
            <button 
              className={`tab-button ${visualization === 'base-peak' ? 'active' : ''}`}
              onClick={() => switchVisualization('base-peak')}
            >
              Базово-пікові компоненти
            </button>
          </div>
          
          <div className="groups-container">
            <div className="visualization-container full-width">
              {renderVisualization()}
            </div>
          </div>
        </>
      )}
      
      {!loading && groups.length === 0 && (
        <div className="placeholder">
          Налаштуйте параметри та натисніть кнопку для формування груп
        </div>
      )}
    </div>
  );
};

export default GroupingView; 