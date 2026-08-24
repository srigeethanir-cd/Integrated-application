import React from 'react';

interface Task {
  id: number;
  title: string;
}

interface DashboardProps {
  tasks: Task[];
}

const Dashboard: React.FC<DashboardProps> = ({ tasks }) => {
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="h-16 bg-primary text-white p-4 text-center">
        <h1 className="text-lg font-bold">Dashboard</h1>
      </header>

      {/* Hero */}
      <section className="h-48 bg-secondary p-4 text-center">
        <h2 className="text-lg font-bold">Your Tasks</h2>
      </section>

      {/* Content */}
      <main className="flex-1 p-4 overflow-y-auto">
        <ul>
          {tasks.map((task) => (
            <li key={task.id} className="bg-white p-4 mb-4 rounded">
              <h3 className="text-lg font-bold">{task.title}</h3>
            </li>
          ))}
        </ul>
        <p className="text-lg font-bold">Task Count: {tasks.length}</p>
      </main>

      {/* Footer */}
      <footer className="h-12 bg-primary text-white p-4 text-center">
        <p>&copy; 2024 Dashboard</p>
      </footer>
    </div>
  );
};

export default Dashboard;