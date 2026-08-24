import React, { useState } from 'react';

interface UserStory {
  story_key: string;
  epic_key: string;
  title: string;
  acceptance_criteria: string[];
}

interface LayoutRules {
  type: string;
  orientation: string;
  components: {
    id: number;
    type: string;
    x: number;
    y: number;
    width: number;
    height: number;
  }[];
}

interface ColorsPalette {
  primary: string;
  secondary: string;
  background: string;
  text: string;
}

interface DesignTokens {
  spacing: {
    small: number;
    medium: number;
    large: number;
  };
  corners: {
    small: number;
    medium: number;
    large: number;
  };
}

const userStories: UserStory[] = [
  {
    story_key: 'US101',
    epic_key: 'EP001',
    title: 'Secure Member Login Integration',
    acceptance_criteria: ['Validate email format', 'Secure password field input'],
  },
  {
    story_key: 'US102',
    epic_key: 'EP001',
    title: 'Member Registration Scaffolding',
    acceptance_criteria: ['Validate password confirmation match'],
  },
];

const layoutRules: LayoutRules = {
  type: 'mobile',
  orientation: 'portrait',
  components: [
    { id: 1, type: 'header', x: 0, y: 0, width: 375, height: 64 },
    { id: 2, type: 'hero_image', x: 0, y: 64, width: 375, height: 200 },
    { id: 3, type: 'button', x: 100, y: 300, width: 175, height: 50 },
    { id: 4, type: 'footer', x: 0, y: 450, width: 375, height: 50 },
  ],
};

const colorsPalette: ColorsPalette = {
  primary: '#3498db',
  secondary: '#f1c40f',
  background: '#ffffff',
  text: '#333333',
};

const designTokens: DesignTokens = {
  spacing: {
    small: 8,
    medium: 16,
    large: 24,
  },
  corners: {
    small: 4,
    medium: 8,
    large: 12,
  },
};

const App: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');

  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(event.target.value);
  };

  const handlePasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(event.target.value);
  };

  const handlePasswordConfirmationChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPasswordConfirmation(event.target.value);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // Validate email format
    if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i.test(email)) {
      alert('Invalid email format');
      return;
    }
    // Secure password field input
    if (password.length < 8) {
      alert('Password must be at least 8 characters long');
      return;
    }
    // Validate password confirmation match
    if (password !== passwordConfirmation) {
      alert('Passwords do not match');
      return;
    }
    // Submit form
    console.log('Form submitted');
  };

  return (
    <div
      style={{
        backgroundColor: colorsPalette.background,
        height: '100vh',
        width: '100vw',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <header
        style={{
          width: layoutRules.components[0].width,
          height: layoutRules.components[0].height,
          backgroundColor: colorsPalette.primary,
          color: colorsPalette.text,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <h1>Secure Member Login Integration</h1>
      </header>
      <div
        style={{
          width: layoutRules.components[1].width,
          height: layoutRules.components[1].height,
          backgroundColor: colorsPalette.secondary,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <img src="hero_image.jpg" alt="Hero Image" />
      </div>
      <form
        onSubmit={handleSubmit}
        style={{
          width: layoutRules.components[2].width,
          height: layoutRules.components[2].height,
          backgroundColor: colorsPalette.background,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <input
          type="email"
          value={email}
          onChange={handleEmailChange}
          placeholder="Email"
          style={{
            width: '100%',
            height: '40px',
            marginBottom: designTokens.spacing.small,
            padding: designTokens.spacing.small,
            borderRadius: designTokens.corners.small,
            border: '1px solid #ccc',
          }}
        />
        <input
          type="password"
          value={password}
          onChange={handlePasswordChange}
          placeholder="Password"
          style={{
            width: '100%',
            height: '40px',
            marginBottom: designTokens.spacing.small,
            padding: designTokens.spacing.small,
            borderRadius: designTokens.corners.small,
            border: '1px solid #ccc',
          }}
        />
        <input
          type="password"
          value={passwordConfirmation}
          onChange={handlePasswordConfirmationChange}
          placeholder="Confirm Password"
          style={{
            width: '100%',
            height: '40px',
            marginBottom: designTokens.spacing.small,
            padding: designTokens.spacing.small,
            borderRadius: designTokens.corners.small,
            border: '1px solid #ccc',
          }}
        />
        <button
          type="submit"
          style={{
            width: '100%',
            height: '40px',
            backgroundColor: colorsPalette.primary,
            color: colorsPalette.text,
            padding: designTokens.spacing.small,
            borderRadius: designTokens.corners.small,
            border: 'none',
          }}
        >
          Submit
        </button>
      </form>
      <footer
        style={{
          width: layoutRules.components[3].width,
          height: layoutRules.components[3].height,
          backgroundColor: colorsPalette.primary,
          color: colorsPalette.text,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <p>&copy; 2024 Secure Member Login Integration</p>
      </footer>
    </div>
  );
};

export default App;