import React from 'react';
import './Sidebar.css';

interface SidebarProps {
  onPageChange: (page: 'grouping' | 'saved-groupings' | 'help') => void;
  currentPage: 'grouping' | 'saved-groupings' | 'help';
}

const Sidebar: React.FC<SidebarProps> = ({ onPageChange, currentPage }) => {
  return (
    <nav className="sidebar">
      <ul className="nav-list">
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