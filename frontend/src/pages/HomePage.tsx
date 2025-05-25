import React from 'react';
import './HomePage.css';

interface HomePageProps {
  onPageChange: (page: 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization' | 'raw-metrics') => void;
}

const HomePage: React.FC<HomePageProps> = ({ onPageChange }) => {
  return (
    <div className="home-page">
      <h1>Система для аналізу та групування мікросервісів</h1>
      
      <div className="features-grid">
        <div className="feature-card" onClick={() => onPageChange('normalization')}>
          <div className="feature-icon">
            <i className="fas fa-chart-bar"></i>
          </div>
          <h3>Нормалізація</h3>
          <p>Нормалізація даних мікросервісів для подальшого аналізу</p>
        </div>

        <div className="feature-card" onClick={() => onPageChange('autonormalization')}>
          <div className="feature-icon">
            <i className="fas fa-magic"></i>
          </div>
          <h3>Автонормалізація</h3>
          <p>Автоматична нормалізація метрик на основі стандартної конфігурації</p>
        </div>

        <div className="feature-card" onClick={() => onPageChange('grouping')}>
          <div className="feature-icon">
            <i className="fas fa-object-group"></i>
          </div>
          <h3>Групування</h3>
          <p>Автоматичне групування мікросервісів на основі навантаження</p>
        </div>

        <div className="feature-card" onClick={() => onPageChange('saved-groupings')}>
          <div className="feature-icon">
            <i className="fas fa-save"></i>
          </div>
          <h3>Збережені групування</h3>
          <p>Перегляд та аналіз збережених результатів групування</p>
        </div>

        <div className="feature-card" onClick={() => onPageChange('help')}>
          <div className="feature-icon">
            <i className="fas fa-question-circle"></i>
          </div>
          <h3>Довідка</h3>
          <p>Інструкції та інформація про використання системи</p>
        </div>

        <div className="feature-card" onClick={() => onPageChange('raw-metrics')}>
          <div className="feature-icon">
            <i className="fas fa-table"></i>
          </div>
          <h3>Сирі метрики</h3>
          <p>Перегляд всіх сирих метрик у вигляді таблиці</p>
        </div>
      </div>
    </div>
  );
};

export default HomePage; 