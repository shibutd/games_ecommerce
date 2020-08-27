import React from 'react';
import ReactDOM from 'react-dom';
import "@babel/polyfill";
import Dashboard from './Dashboard';
import { DashboardContextProvider } from './context';

export default function AppDashboard() {
  return (
    <DashboardContextProvider>
      <Dashboard />
    </DashboardContextProvider>
  );
}

const container = document.getElementById('react-dashboard');
ReactDOM.render(<AppDashboard />, container);
