import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import './App.css';

// Імпорт компонентів сторінок
import Header from './components/Header.tsx';
import Sidebar from './components/Sidebar.tsx';
import Dashboard from './pages/Dashboard.tsx';
// Тимчасово приховано
// import MicroserviceView from './pages/MicroserviceView.tsx';
import GroupingView from './pages/GroupingView.tsx';
// import StabilityView from './pages/StabilityView.tsx';

const App: React.FC = () => {
  return (
    <Router>
      <div className="app">
        <Header />
        <div className="main-container">
          <Sidebar />
          <main className="content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              {/* Тимчасово приховано
              <Route path="/microservices" element={<MicroserviceView />} />
              */}
              <Route path="/grouping" element={<GroupingView />} />
              {/* Тимчасово приховано 
              <Route path="/stability" element={<StabilityView />} />
              */}
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
};

export default App; 