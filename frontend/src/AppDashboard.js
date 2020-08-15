import React from 'react';
import ReactDOM from 'react-dom';
import Dashboard from './Dashboard';
import { UserContextProvider, DataContextProvider } from './context';

export default function App() {
  return (
    <UserContextProvider>
      <DataContextProvider>
       <Dashboard />
     </DataContextProvider>
    </UserContextProvider>
  );
}

const container = document.getElementById('react-dashboard');
ReactDOM.render(<App />, container);
