import React from 'react';

interface UserStory {
  id: string;
  actor: string;
  title: string;
  epic_key: string;
  priority: string;
  story_key: string;
  description: string;
  acceptance_criteria: string[];
}

interface DashboardProps {
  userStory: UserStory;
}

const Dashboard: React.FC<DashboardProps> = ({ userStory }) => {
  return (
    <div className="h-screen bg-background p-8">
      <h1 className="text-3xl text-primary mb-4">{userStory.title}</h1>
      <p className="text-lg text-primary mb-8">{userStory.description}</p>
      <div className="flex flex-col">
        <h2 className="text-2xl text-primary mb-4">Tasks:</h2>
        <ul>
          {userStory.acceptance_criteria.map((task, index) => (
            <li key={index} className="text-lg text-primary mb-2">
              {task}
            </li>
          ))}
        </ul>
        <p className="text-lg text-primary mt-4">
          Task count: {userStory.acceptance_criteria.length}
        </p>
      </div>
    </div>
  );
};

const userStory: UserStory = {
  id: "US003",
  actor: "User",
  title: "View Dashboard",
  epic_key: "EP001",
  priority: "Medium",
  story_key: "US003",
  description: "As a user, I want to see my tasks on a dashboard.",
  acceptance_criteria: ["Display tasks list", "Show task count"]
};

const App = () => {
  return <Dashboard userStory={userStory} />;
};

export default App;