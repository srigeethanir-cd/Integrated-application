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

interface Props {
  userStory: UserStory;
}

const Dashboard: React.FC<Props> = ({ userStory }) => {
  return (
    <div className="max-w-md mx-auto p-4 md:p-6 lg:p-8 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-primary-color mb-4">{userStory.title}</h2>
      <p className="text-lg text-text-color mb-6">{userStory.description}</p>
      <div className="flex flex-col">
        <div className="flex justify-between mb-4">
          <h3 className="text-lg font-bold text-primary-color">Tasks:</h3>
          <p className="text-lg text-text-color">Count: {userStory.acceptance_criteria.length}</p>
        </div>
        <ul>
          {userStory.acceptance_criteria.map((criterion, index) => (
            <li key={index} className="text-lg text-text-color mb-2">{criterion}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;