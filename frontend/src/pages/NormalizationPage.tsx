import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './NormalizationPage.css';

// Інтерфейси для даних
interface AvailableOptions {
    dates: string[];
    times: { [date: string]: string[] };
    metric_types: string[];
}

const NormalizationPage: React.FC = () => {
    // Стани для даних
    const [availableOptions, setAvailableOptions] = useState<AvailableOptions | null>(null);
    const [selectedMetricType, setSelectedMetricType] = useState<string>('');
    const [selectedDate, setSelectedDate] = useState<string>('');
    const [selectedTime, setSelectedTime] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [resultMessage, setResultMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Завантаження доступних опцій при монтуванні компонента
    useEffect(() => {
        fetchAvailableOptions();
    }, []);

    // Функція для отримання доступних опцій з API
    const fetchAvailableOptions = async () => {
        try {
            setIsLoading(true);
            const response = await axios.get('http://localhost:8000/api/metrics/raw-data-options');
            setAvailableOptions(response.data);
            setError(null);
        } catch (error) {
            console.error('Помилка при отриманні доступних опцій:', error);
            setError('Помилка при завантаженні даних. Спробуйте оновити сторінку.');
        } finally {
            setIsLoading(false);
        }
    };

    // Функція для нормалізації даних
    const normalizeData = async () => {
        if (!selectedMetricType || !selectedDate || !selectedTime) {
            setError('Будь ласка, виберіть всі необхідні параметри');
            return;
        }

        try {
            setIsLoading(true);
            setResultMessage(null);
            setError(null);

            const response = await axios.post(
                `http://localhost:8000/api/metrics/normalize-percentage?metric_type=${selectedMetricType}&date=${selectedDate}&time=${selectedTime}`
            );

            setResultMessage(response.data.message);
        } catch (error) {
            console.error('Помилка при нормалізації даних:', error);
            if (axios.isAxiosError(error) && error.response) {
                setError(error.response.data.detail || 'Помилка при нормалізації даних');
            } else {
                setError('Помилка при нормалізації даних. Спробуйте ще раз.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    // Обробники змін вибраних значень
    const handleMetricTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newMetricType = e.target.value;
        setSelectedMetricType(newMetricType);
        setSelectedDate('');
        setSelectedTime('');
    };

    const handleDateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newDate = e.target.value;
        setSelectedDate(newDate);
        setSelectedTime('');
    };

    return (
        <div className="normalization-page">
            <h1>Нормалізація даних мікросервісів</h1>
            
            <div className="normalization-form">
                <div className="form-group">
                    <label htmlFor="metric-type">Тип метрики:</label>
                    <select 
                        id="metric-type"
                        value={selectedMetricType}
                        onChange={handleMetricTypeChange}
                        disabled={isLoading || !availableOptions}
                    >
                        <option value="">Виберіть тип метрики</option>
                        {availableOptions?.metric_types.map((type) => (
                            <option key={type} value={type}>{type}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="date">Дата:</label>
                    <select 
                        id="date"
                        value={selectedDate}
                        onChange={handleDateChange}
                        disabled={isLoading || !selectedMetricType || !availableOptions}
                    >
                        <option value="">Виберіть дату</option>
                        {availableOptions?.dates.map((date) => (
                            <option key={date} value={date}>{date}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="time">Час:</label>
                    <select 
                        id="time"
                        value={selectedTime}
                        onChange={(e) => setSelectedTime(e.target.value)}
                        disabled={isLoading || !selectedDate || !availableOptions}
                    >
                        <option value="">Виберіть час</option>
                        {selectedDate && availableOptions?.times[selectedDate]?.map((time) => (
                            <option key={time} value={time}>{time}</option>
                        ))}
                    </select>
                </div>

                <button 
                    className="normalize-button"
                    onClick={normalizeData}
                    disabled={isLoading || !selectedMetricType || !selectedDate || !selectedTime}
                >
                    {isLoading ? 'Обробка...' : 'Нормалізувати дані'}
                </button>
            </div>

            {resultMessage && (
                <div className="result-message success">
                    {resultMessage}
                </div>
            )}

            {error && (
                <div className="result-message error">
                    {error}
                </div>
            )}

            <div className="info-box">
                <h3>Про нормалізацію даних</h3>
                <p>
                    Ця функція нормалізує сирі дані метрик мікросервісів у діапазон від 0 до 100 (відсотки).
                    Оберіть тип метрики, дату та час, щоб вибрати набір даних для нормалізації.
                </p>
                <p>
                    Після нормалізації дані будуть збережені в базі даних і доступні для подальшої обробки та групування.
                </p>
            </div>
        </div>
    );
};

export default NormalizationPage; 