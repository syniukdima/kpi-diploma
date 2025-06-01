import React, { useState, useEffect } from 'react';
import './SavedGroupingsPage.css';
import axios from 'axios';

const API_BASE_URL = 'https://syniukdmytro.online';

// Константи для параметрів, які використовуються в запитах
const DEFAULT_MAX_GROUP_SIZE = 3;
const DEFAULT_STABILITY_THRESHOLD = 20;

interface GroupingData {
  date: string;
  time: string;
  metric_type: string;
  num_groups: number;
}

interface GroupService {
  service_name: string;
  component_type: string;
}

interface GroupStatistics {
  group_id: number;
  service_count: number;
  services: { name: string, component_type: string }[];
  mean_load: number;
  peak_load: number;
  coefficient_of_variation: number;
  total_load: number[];
}

// Інтерфейс статистики для відповідності до GroupingView
interface GroupStatisticsForView {
  group_id: number;
  num_services: number;
  mean_load: number;
  peak_load: number;
  stability: number;
  services: string[];
}

type VisualizationType = 'load' | 'stability' | 'statistics' | 'distribution' | 'microservices' | 'base-peak';

const SavedGroupingsPage: React.FC = () => {
  const [groupings, setGroupings] = useState<GroupingData[]>([]);
  const [selectedGrouping, setSelectedGrouping] = useState<GroupingData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showVisualizations, setShowVisualizations] = useState<boolean>(false);
  
  // Стан для візуалізацій
  const [visualization, setVisualization] = useState<VisualizationType>('load');
  const [groups, setGroups] = useState<number[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);
  
  // Стан для зображень графіків
  const [microservicesChartUrl, setMicroservicesChartUrl] = useState<string | null>(null);
  const [loadingMicroservices, setLoadingMicroservices] = useState<boolean>(false);
  
  const [loadChartUrl, setLoadChartUrl] = useState<string | null>(null);
  const [loadingLoadChart, setLoadingLoadChart] = useState<boolean>(false);
  
  const [stabilityChartUrl, setStabilityChartUrl] = useState<string | null>(null);
  const [loadingStabilityChart, setLoadingStabilityChart] = useState<boolean>(false);
  
  const [distributionChartUrl, setDistributionChartUrl] = useState<string | null>(null);
  const [loadingDistributionChart, setLoadingDistributionChart] = useState<boolean>(false);
  
  const [basePeakChartUrl, setBasePeakChartUrl] = useState<string | null>(null);
  const [loadingBasePeak, setLoadingBasePeak] = useState<boolean>(false);
  
  // Змінити тип з одиничної статистики на масив для відповідності GroupingView
  const [groupStatistics, setGroupStatistics] = useState<GroupStatisticsForView[]>([]);
  const [loadingStatistics, setLoadingStatistics] = useState<boolean>(false);

  // Додаємо стан для зберігання сервісів, які можна розділити
  const [splitServices, setSplitServices] = useState<string[]>([]);
  const [selectedServiceForBasePeak, setSelectedServiceForBasePeak] = useState<string | null>(null);

  // Завантаження списку збережених варіантів групування
  useEffect(() => {
    const fetchGroupings = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/api/saved-groupings/groupings`);
        setGroupings(response.data);
        setError(null);
      } catch (err) {
        setError('Помилка завантаження збережених групувань');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchGroupings();
  }, []);

  // Завантаження груп для вибраного варіанту групування
  useEffect(() => {
    if (!selectedGrouping) {
      setGroups([]);
      return;
    }

    const fetchGroups = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/api/saved-groupings/groups`, {
          params: {
            date: selectedGrouping.date,
            time: selectedGrouping.time,
            metric_type: selectedGrouping.metric_type
          }
        });
        setGroups(response.data);
        // Встановлюємо першу групу як вибрану за замовчуванням
        if (response.data && response.data.length > 0) {
          setSelectedGroup(response.data[0]);
        }
        setError(null);
      } catch (err) {
        setError('Помилка завантаження груп');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchGroups();
  }, [selectedGrouping]);

  // Обробник вибору варіанту групування
  const handleGroupingSelect = (grouping: GroupingData) => {
    setSelectedGrouping(grouping);
    // При виборі нового варіанту приховуємо візуалізації
    setShowVisualizations(false);
    
    // Скидаємо всі графіки
    setMicroservicesChartUrl(null);
    setLoadChartUrl(null);
    setStabilityChartUrl(null);
    setDistributionChartUrl(null);
    setBasePeakChartUrl(null);
    setGroupStatistics([]);
  };

  // Обробник натискання на кнопку перегляду результатів
  const handleViewResults = () => {
    if (!selectedGrouping) {
      alert('Спочатку виберіть варіант групування');
      return;
    }

    // Показуємо візуалізації
    setShowVisualizations(true);
    
    // Встановлюємо початкову вкладку та завантажуємо дані для неї
    setVisualization('load');
    fetchLoadChart();
    
    // Завантажуємо дані для інших вкладок у фоновому режимі
    setTimeout(() => {
      fetchMicroservicesChart();
      fetchStabilityChart();
      fetchGroupStatistics();
      fetchSplitServices();
    }, 100);
  };

  // Перемикання візуалізації та завантаження відповідних даних
  const switchVisualization = (visType: VisualizationType) => {
    setVisualization(visType);
    
    // Скидаємо попередні дані при зміні вкладки
    setSelectedGroup(null);
    setDistributionChartUrl(null);
    setLoadChartUrl(null);
    setStabilityChartUrl(null);
    setGroupStatistics([]);
    
    // Завантаження даних для нової вкладки
    if (showVisualizations && selectedGrouping) {
      switch (visType) {
        case 'load':
          fetchLoadChart();
          break;
        case 'stability':
          fetchStabilityChart();
          break;
        case 'statistics':
          fetchGroupStatistics();
          break;
        case 'distribution':
          // Для distribution не робимо автоматичний запит, чекаємо вибору групи
          break;
      }
    }
  };

  // Завантаження графіку мікросервісів
  const fetchMicroservicesChart = async () => {
    if (!selectedGrouping) return;
    
    try {
      setLoadingMicroservices(true);
      
      const { date, time, metric_type } = selectedGrouping;
      
      // Формування URL із параметрами запиту
      const requestUrl = new URL(`${API_BASE_URL}/api/visualization/microservices-chart`);
      requestUrl.searchParams.append('date', date);
      requestUrl.searchParams.append('time', time);
      requestUrl.searchParams.append('metric_type', metric_type);
      
      // Виконання запиту
      const response = await axios.get(requestUrl.toString(), { responseType: 'blob' });
      
      // Створення URL для зображення
      const blob = new Blob([response.data], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);
      setMicroservicesChartUrl(imageUrl);
    } catch (err) {
      console.error('Помилка при отриманні графіку мікросервісів:', err);
    } finally {
      setLoadingMicroservices(false);
    }
  };
  
  // Завантаження графіку навантаження груп
  const fetchLoadChart = async () => {
    if (!selectedGrouping) return;
    
    try {
      setLoadingLoadChart(true);
      
      const { date, time, metric_type } = selectedGrouping;
      
      // Формування URL із параметрами запиту
      const requestUrl = new URL(`${API_BASE_URL}/api/visualization/group-load`);
      requestUrl.searchParams.append('date', date);
      requestUrl.searchParams.append('time', time);
      requestUrl.searchParams.append('metric_type', metric_type);
      
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
  
  // Завантаження графіку стабільності
  const fetchStabilityChart = async () => {
    if (!selectedGrouping) return;
    
    try {
      setLoadingStabilityChart(true);
      
      const { date, time, metric_type } = selectedGrouping;
      
      // Формування URL із параметрами запиту
      const requestUrl = new URL(`${API_BASE_URL}/api/visualization/stability-direct`);
      requestUrl.searchParams.append('date', date);
      requestUrl.searchParams.append('time', time);
      requestUrl.searchParams.append('metric_type', metric_type);
      
      // Виконання запиту
      const response = await axios.get(requestUrl.toString(), { responseType: 'blob' });
      
      // Створення URL для зображення
      const blob = new Blob([response.data], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);
      setStabilityChartUrl(imageUrl);
    } catch (err) {
      console.error('Помилка при отриманні графіку стабільності груп:', err);
    } finally {
      setLoadingStabilityChart(false);
    }
  };
  
  // Функція для завантаження списку сервісів, які можна розділити
  const fetchSplitServices = async () => {
    if (!selectedGrouping) return;
    
    try {
      setLoadingBasePeak(true);
      
      const { date, time, metric_type } = selectedGrouping;
      
      // Формування URL із параметрами запиту для отримання списку сервісів
      // Додаємо параметри max_group_size та stability_threshold як в GroupingView
      const findSplitServicesUrl = new URL(`${API_BASE_URL}/api/grouping/find-split-services`);
      findSplitServicesUrl.searchParams.append('metric_type', metric_type);
      findSplitServicesUrl.searchParams.append('date', date);
      findSplitServicesUrl.searchParams.append('time', time);
      findSplitServicesUrl.searchParams.append('max_group_size', DEFAULT_MAX_GROUP_SIZE.toString());
      findSplitServicesUrl.searchParams.append('stability_threshold', DEFAULT_STABILITY_THRESHOLD.toString());
      
      console.log('Запит на отримання розділених сервісів:', findSplitServicesUrl.toString());
      
      const splitResponse = await axios.get(findSplitServicesUrl.toString());
      console.log('Відповідь split services:', splitResponse.data);
      
      // Обробка відповіді - точно так само, як в GroupingView
      const foundSplitServices = splitResponse.data.split_services || [];
      setSplitServices(foundSplitServices);
      
      // Якщо є розділені мікросервіси, вибираємо перший і отримуємо для нього графік
      if (foundSplitServices.length > 0) {
        setSelectedServiceForBasePeak(foundSplitServices[0]);
        await fetchBasePeakChart(foundSplitServices[0]);
      } else {
        console.log('Не знайдено розділених сервісів');
      }
    } catch (err) {
      console.error('Помилка при отриманні списку розділених сервісів:', err);
      setSplitServices([]);
    } finally {
      setLoadingBasePeak(false);
    }
  };
  
  // Завантаження графіку базово-пікових компонентів
  const fetchBasePeakChart = async (serviceName?: string) => {
    if (!selectedGrouping) return;
    
    const serviceToUse = serviceName || selectedServiceForBasePeak;
    if (!serviceToUse) {
      console.error('Не вказано назву сервісу для отримання графіку');
      return;
    }
    
    try {
      setLoadingBasePeak(true);
      
      const { date, time, metric_type } = selectedGrouping;
      
      // Формування URL із параметрами запиту - точно так само, як в GroupingView
      const chartUrl = new URL(`${API_BASE_URL}/api/visualization/base-peak-component`);
      chartUrl.searchParams.append('service_name', serviceToUse);
      chartUrl.searchParams.append('metric_type', metric_type);
      chartUrl.searchParams.append('date', date);
      chartUrl.searchParams.append('time', time);
      
      console.log('Запит на отримання графіку базово-пікових компонентів:', chartUrl.toString());
      
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
  
  // Завантаження графіку розподілу навантаження
  const fetchDistributionChart = async (groupId: number) => {
    if (!selectedGrouping) return;
    
    try {
      setLoadingDistributionChart(true);
      
      const { date, time, metric_type } = selectedGrouping;
      
      // Формування URL із параметрами запиту
      const requestUrl = new URL(`${API_BASE_URL}/api/visualization/group-load-distribution`);
      requestUrl.searchParams.append('group_id', groupId.toString());
      requestUrl.searchParams.append('date', date);
      requestUrl.searchParams.append('time', time);
      requestUrl.searchParams.append('metric_type', metric_type);
      
      // Виконання запиту
      const response = await axios.get(requestUrl.toString(), { responseType: 'blob' });
      
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
  
  // Завантаження статистики для всіх груп
  const fetchGroupStatistics = async () => {
    if (!selectedGrouping) return;
    
    try {
      setLoadingStatistics(true);
      
      const { date, time, metric_type } = selectedGrouping;
      
      // Формування URL із параметрами запиту
      const requestUrl = new URL(`${API_BASE_URL}/api/visualization/group-statistics`);
      requestUrl.searchParams.append('date', date);
      requestUrl.searchParams.append('time', time);
      requestUrl.searchParams.append('metric_type', metric_type);
      
      // Виконання запиту
      const response = await axios.get(requestUrl.toString());
      
      // Встановлюємо статистику
      if (response.data && response.data.statistics) {
        setGroupStatistics(response.data.statistics);
      } else {
        console.error('Неочікуваний формат даних статистики', response.data);
        setGroupStatistics([]);
      }
    } catch (err) {
      console.error('Помилка при отриманні статистики груп:', err);
      setGroupStatistics([]);
    } finally {
      setLoadingStatistics(false);
    }
  };

  // Функція для визначення класу рядка (вибраний чи ні)
  const getRowClass = (grouping: GroupingData) => {
    if (selectedGrouping && 
        selectedGrouping.date === grouping.date && 
        selectedGrouping.time === grouping.time && 
        selectedGrouping.metric_type === grouping.metric_type) {
      return 'selected';
    }
    return '';
  };

  // Рендерінг візуалізацій
  const renderVisualization = () => {
    if (!selectedGrouping || !showVisualizations) {
      return null;
    }

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
                  onClick={fetchLoadChart}
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
                      <li><strong>Середнє навантаження:</strong> {stats.mean_load !== undefined ? stats.mean_load.toFixed(2) : 'Н/Д'}</li>
                      <li><strong>Пікове навантаження:</strong> {stats.peak_load !== undefined ? stats.peak_load.toFixed(2) : 'Н/Д'}</li>
                      <li><strong>Коефіцієнт стабільності (%):</strong> {stats.stability !== undefined ? stats.stability.toFixed(2) : 'Н/Д'}</li>
                    </ul>
                    <h4>Мікросервіси:</h4>
                    <ul className="services-list-simple">
                      {Array.isArray(stats.services) ? (
                        stats.services.map((service, idx) => (
                          <li key={idx}>{service}</li>
                        ))
                      ) : (
                        <li>Немає даних про мікросервіси</li>
                      )}
                    </ul>
                  </div>
                ))}
              </div>
            ) : (
              <div className="placeholder">
                <button 
                  className="fetch-button"
                  onClick={fetchGroupStatistics}
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
                  const groupId = parseInt(e.target.value);
                  if (!isNaN(groupId)) {
                    setSelectedGroup(groupId);
                    setDistributionChartUrl(null);
                    fetchDistributionChart(groupId);
                  }
                }}
              >
                <option value="">Оберіть групу</option>
                {groups.map(groupId => (
                  <option key={groupId} value={groupId}>Група {groupId}</option>
                ))}
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
                  onClick={() => selectedGroup && fetchDistributionChart(selectedGroup)}
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
            ) : microservicesChartUrl ? (
              <div className="microservices-chart">
                <div className="chart-image">
                  <img 
                    src={microservicesChartUrl} 
                    alt="Часові ряди мікросервісів" 
                    className="microservices-chart-img" 
                    style={{ width: '100%', maxHeight: '600px', objectFit: 'contain' }}
                  />
                </div>
              </div>
            ) : (
              <div className="placeholder">
                <button 
                  className="fetch-button"
                  onClick={fetchMicroservicesChart}
                >
                  Завантажити графік мікросервісів
                </button>
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
    <div className="saved-groupings-page">
      <h2>Збережені варіанти групування</h2>

      {error && <div className="error-message">{error}</div>}

      <div className="groupings-table-fullwidth">
        <h3>Доступні варіанти групування</h3>
        <div className="table-container">
          <table className="groupings-table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Час</th>
                <th>Тип метрики</th>
                <th>Кількість груп</th>
              </tr>
            </thead>
            <tbody>
              {loading && !groupings.length ? (
                <tr>
                  <td colSpan={4}>Завантаження...</td>
                </tr>
              ) : groupings.length === 0 ? (
                <tr>
                  <td colSpan={4}>Немає збережених варіантів групування</td>
                </tr>
              ) : (
                groupings.map((grouping, index) => (
                  <tr 
                    key={index} 
                    onClick={() => handleGroupingSelect(grouping)} 
                    className={getRowClass(grouping)}
                  >
                    <td>{grouping.date}</td>
                    <td>{grouping.time}</td>
                    <td>{grouping.metric_type}</td>
                    <td>{grouping.num_groups}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="buttons">
          <button 
            className="fetch-button" 
            onClick={handleViewResults}
            disabled={!selectedGrouping}
          >
            Переглянути результати
          </button>
        </div>
      </div>

      {showVisualizations && (
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
          
          <div className="visualization-container full-width">
              {renderVisualization()}
          </div>
        </>
      )}
    </div>
  );
};

export default SavedGroupingsPage; 