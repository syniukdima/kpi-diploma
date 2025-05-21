import React from 'react';
import './Header.css';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="logo">
        <h1>Аналіз мікросервісів</h1>
      </div>
      <div className="user-info">
        <span>Дипломний проект</span>
      </div>
    </header>
  );
};

export default Header; 