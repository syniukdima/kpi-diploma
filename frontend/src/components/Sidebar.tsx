import React from 'react';
import './Sidebar.css';

interface SidebarProps {
  onPageChange: (page: 'home' | 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization') => void;
  currentPage: 'home' | 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization';
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
        <li>
          <a 
            href="#" 
            className={currentPage === 'autonormalization' ? 'active' : ''} 
            onClick={(e) => {
              e.preventDefault();
              onPageChange('autonormalization');
            }}
          >
            Автонормалізація
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