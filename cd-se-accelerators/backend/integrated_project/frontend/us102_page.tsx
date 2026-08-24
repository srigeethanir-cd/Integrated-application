typescript
// Component.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface DashboardData {
  employees: number;
  departments: number;
  locations: number;
}

const Component: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/dashboard');
        setDashboardData(response.data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchDashboardData();
  }, []);

  if (!dashboardData) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Employee Dashboard & Analytics</h1>
      <p>Employees: {dashboardData.employees}</p>
      <p>Departments: {dashboardData.departments}</p>
      <p>Locations: {dashboardData.locations}</p>
    </div>
  );
};

export default Component;