import React from 'react';
import './Header.css';

interface HeaderProps {
  onHomeClick: () => void;
  onMenuToggle?: () => void;
  showMenuButton?: boolean;
}

const Header: React.FC<HeaderProps> = ({ onHomeClick, onMenuToggle, showMenuButton = false }) => {
  return (
    <header className="header">
      <div className="logo">
        <a href="#" className="home-link" onClick={(e) => {
          e.preventDefault();
          onHomeClick();
        }}>
          <h1>Групування мікросервісів</h1>
        </a>
      </div>
      <div className="header-right">
        <div className="user-info">
          Система аналізу навантаження
        </div>
        {showMenuButton && (
          <button 
            className="mobile-menu-toggle-header"
            onClick={onMenuToggle}
            aria-label="Відкрити меню"
          >
            ☰
          </button>
        )}
      </div>
    </header>
  );
};

export default Header; 