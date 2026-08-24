import React, { useState } from 'react';
import { UserStory } from '../types/UserStory';
import { LayoutRules } from '../types/LayoutRules';
import { ColorsPalette } from '../types/ColorsPalette';
import { DesignTokens } from '../types/DesignTokens';

interface Props {
  userStories: UserStory[];
  layoutRules: LayoutRules;
  colorsPalette: ColorsPalette;
  designTokens: DesignTokens;
}

const UserRegistrationComponent: React.FC<Props> = ({
  userStories,
  layoutRules,
  colorsPalette,
  designTokens,
}) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleRegister = () => {
    // Register user logic
    console.log('Register user:', name, email, password);
  };

  const handleLogin = () => {
    // Login user logic
    console.log('Login user:', email, password);
    setIsLoggedIn(true);
  };

  return (
    <div
      className="h-screen flex flex-col"
      style={{
        backgroundColor: colorsPalette.background,
      }}
    >
      {/* Navigation Bar */}
      <div
        className="h-14 flex justify-between items-center px-4"
        style={{
          backgroundColor: colorsPalette.primary,
          height: layoutRules.components[0].height,
        }}
      >
        <h1 className="text-2xl text-white">Task Manager</h1>
      </div>

      {/* Hero Section */}
      <div
        className="h-48 flex justify-center items-center"
        style={{
          height: layoutRules.components[1].height,
        }}
      >
        <h1 className="text-3xl text-center text-primary">
          {userStories[0].title}
        </h1>
      </div>

      {/* List Section */}
      <div
        className="flex-1 overflow-y-scroll px-4 py-4"
        style={{
          height: layoutRules.components[2].height,
        }}
      >
        {userStories.map((story) => (
          <div key={story.id} className="mb-4">
            <h2 className="text-xl text-primary">{story.title}</h2>
            <p className="text-lg text-gray-600">{story.description}</p>
            <ul>
              {story.acceptance_criteria.map((criterion) => (
                <li key={criterion} className="text-lg text-gray-600">
                  {criterion}
                </li>
              ))}
            </ul>
          </div>
        ))}
        {/* Registration Form */}
        {!isLoggedIn && (
          <div className="mt-4">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Name"
              className="w-full p-2 mb-2 border border-gray-400 rounded"
            />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              className="w-full p-2 mb-2 border border-gray-400 rounded"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full p-2 mb-2 border border-gray-400 rounded"
            />
            <button
              onClick={handleRegister}
              className="w-full p-2 bg-primary text-white rounded"
            >
              Register
            </button>
          </div>
        )}
        {/* Login Form */}
        {isLoggedIn && (
          <div className="mt-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              className="w-full p-2 mb-2 border border-gray-400 rounded"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full p-2 mb-2 border border-gray-400 rounded"
            />
            <button
              onClick={handleLogin}
              className="w-full p-2 bg-primary text-white rounded"
            >
              Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserRegistrationComponent;