import React from 'react';
import { Link } from 'react-router-dom';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  return (
    <div className="dashboard">
      <h2>Вітаємо в системі аналізу мікросервісів</h2>
      
      <div className="dashboard-cards">
        <div className="card">
          <h3>Мікросервіси</h3>
          <p>Перегляд та аналіз окремих мікросервісів</p>
          <Link to="/microservices" className="card-link">Перейти</Link>
        </div>
        
        <div className="card">
          <h3>Групування</h3>
          <p>Формування оптимальних груп мікросервісів</p>
          <Link to="/grouping" className="card-link">Перейти</Link>
        </div>
        
        <div className="card">
          <h3>Стабільність</h3>
          <p>Аналіз стабільності груп</p>
          <Link to="/stability" className="card-link">Перейти</Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 