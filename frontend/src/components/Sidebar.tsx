import React from 'react';
import './Sidebar.css';

interface SidebarProps {
  onPageChange: (page: 'home' | 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization' | 'raw-metrics') => void;
  currentPage: 'home' | 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization' | 'raw-metrics';
}

const Sidebar: React.FC<SidebarProps> = ({ onPageChange, currentPage }) => {
  return (
    <nav className="sidebar">
      <ul className="nav-list">
        <li>
          <a 
            href="#" 
            className={currentPage === 'home' ? 'active' : ''} 
            onClick={(e) => {
              e.preventDefault();
              onPageChange('home');
            }}
          >
            Головна
          </a>
        </li>
        <li>
          <a 
            href="#" 
            className={currentPage === 'normalization' ? 'active' : ''} 
            onClick={(e) => {
              e.preventDefault();
              onPageChange('normalization');
            }}
          >
            Нормалізація
          </a>
        </li>
        <li className={currentPage === 'autonormalization' ? 'active' : ''}>
          <a href="#" onClick={() => onPageChange('autonormalization')}>
            <span>Автонормалізація</span>
          </a>
        </li>
        <li className={currentPage === 'raw-metrics' ? 'active' : ''}>
          <a href="#" onClick={() => onPageChange('raw-metrics')}>
            <span>Сирі метрики</span>
          </a>
        </li>
        <li>
          <a 
            href="#" 
            className={currentPage === 'grouping' ? 'active' : ''} 
            onClick={(e) => {
              e.preventDefault();
              onPageChange('grouping');
            }}
          >
            Групування
          </a>
        </li>
        <li>
          <a 
            href="#" 
            className={currentPage === 'saved-groupings' ? 'active' : ''} 
            onClick={(e) => {
              e.preventDefault();
              onPageChange('saved-groupings');
            }}
          >
            Збережені групування
          </a>
        </li>
        <li>
          <a 
            href="#" 
            className={currentPage === 'help' ? 'active' : ''} 
            onClick={(e) => {
              e.preventDefault();
              onPageChange('help');
            }}
          >
            Довідка
          </a>
        </li>
      </ul>
    </nav>
  );
};

export default Sidebar; 