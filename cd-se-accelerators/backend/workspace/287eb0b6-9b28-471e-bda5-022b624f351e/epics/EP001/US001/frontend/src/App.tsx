import React, { useState } from 'react';

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

const UserRegistration: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userStory, setUserStory] = useState<UserStory>({
    id: "US001",
    actor: "User",
    title: "User Registration",
    epic_key: "EP001",
    priority: "High",
    story_key: "US001",
    description: "As a new user, I want to register so I can manage tasks.",
    acceptance_criteria: ["Register using name, email, password", "Email unique"]
  });

  const handleRegister = () => {
    // Register logic here
    console.log('Registered:', name, email, password);
  };

  return (
    <div className="max-w-md mx-auto p-8 bg-white rounded-lg shadow-md">
      <nav className="flex justify-between mb-4">
        <h1 className="text-lg font-bold text-primary">{userStory.title}</h1>
      </nav>
      <section className="hero-section mb-8">
        <h2 className="text-lg font-bold text-primary mb-2">{userStory.description}</h2>
        <ul>
          {userStory.acceptance_criteria.map((criterion, index) => (
            <li key={index} className="text-sm text-text mb-2">{criterion}</li>
          ))}
        </ul>
      </section>
      <section className="list-section">
        <form onSubmit={handleRegister}>
          <div className="mb-4">
            <label className="block text-sm text-text mb-2" htmlFor="name">Name:</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="block w-full p-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm text-text mb-2" htmlFor="email">Email:</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="block w-full p-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm text-text mb-2" htmlFor="password">Password:</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="block w-full p-2 border border-gray-300 rounded-lg"
            />
          </div>
          <button
            type="submit"
            className="w-full p-2 bg-primary text-white rounded-lg hover:bg-secondary"
          >
            Register
          </button>
        </form>
      </section>
    </div>
  );
};

export default UserRegistration;