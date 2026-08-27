import os
import json
import shutil
from pathlib import Path

SCRATCH_DIR = Path(__file__).resolve().parent / "test_workspace"
os.makedirs(SCRATCH_DIR, exist_ok=True)

def create_small_react_project(dir_path: Path):
    os.makedirs(dir_path / "src" / "components", exist_ok=True)
    os.makedirs(dir_path / "src" / "services", exist_ok=True)

    (dir_path / "package.json").write_text(json.dumps({
        "name": "small-react-app",
        "version": "1.0.0",
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        }
    }))

    (dir_path / "src" / "components" / "SimpleButton.jsx").write_text("""import React, { useState } from 'react';

export const SimpleButton = ({ label, onClick }) => {
  const [clicked, setClicked] = useState(false);

  const handleClick = (e) => {
    setClicked(true);
    if (onClick) onClick(e);
  };

  return (
    <button onClick={handleClick} className="btn">
      {label} - {clicked ? 'Clicked' : 'Idle'}
    </button>
  );
};
""")

def create_large_react_project(dir_path: Path):
    os.makedirs(dir_path / "src" / "components", exist_ok=True)
    os.makedirs(dir_path / "src" / "services", exist_ok=True)
    os.makedirs(dir_path / "src" / "hooks", exist_ok=True)

    (dir_path / "package.json").write_text(json.dumps({
        "name": "large-react-app",
        "version": "2.0.0",
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "axios": "^1.6.0",
            "react-router-dom": "^6.20.0"
        }
    }))

    # Component 1 (Functional Component): LoginForm.jsx
    (dir_path / "src" / "components" / "LoginForm.jsx").write_text("""import React, { useState, useEffect } from 'react';
import { authService } from '../services/authService';

export const LoginForm = ({ onSubmit, initialEmail = '' }) => {
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log("LoginForm mounted");
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await authService.login({ email, password });
      onSubmit(res);
    } catch (err) {
      setError('Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <label htmlFor="email">Email</label>
      <input type="email" name="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      {email === '' && <span className="warning">Email is required</span>}
      <label htmlFor="password">Password</label>
      <input type="password" name="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      {error && <p className="error">{error}</p>}
      <button type="submit">Submit</button>
    </form>
  );
};
""")

    # Component 2 (Class Component): UserProfile.jsx (to cover class components)
    (dir_path / "src" / "components" / "UserProfile.jsx").write_text("""import React from 'react';

export default class UserProfile extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isEditing: false,
      name: props.user?.name || ''
    };
  }

  handleToggleEdit = () => {
    this.setState(state => ({ isEditing: !state.isEditing }));
  };

  render() {
    const { user } = this.props;
    const { isEditing, name } = this.state;
    return (
      <div className="user-profile">
        <h2>Profile</h2>
        {isEditing ? (
          <input value={name} onChange={(e) => this.setState({ name: e.target.value })} />
        ) : (
          <p>Name: {name}</p>
        )}
        <button onClick={this.handleToggleEdit}>
          {isEditing ? 'Save' : 'Edit'}
        </button>
      </div>
    );
  }
}
""")

    # Component 3 (Functional Component with custom hooks, fetch API): Dashboard.jsx
    (dir_path / "src" / "components" / "Dashboard.jsx").write_text("""import React, { useState, useEffect } from 'react';

export const Dashboard = ({ userId }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/dashboard/${userId}`)
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      });
  }, [userId]);

  return (
    <div className="dashboard">
      {loading ? (
        <span className="spinner">Loading...</span>
      ) : (
        <ul>
          {data.map(item => (
            <li key={item.id}>{item.title}</li>
          ))}
        </ul>
      )}
    </div>
  );
};
""")

    # Existing test file
    (dir_path / "src" / "components" / "LoginForm.test.jsx").write_text("""import { render, screen } from '@testing-library/react';
import { LoginForm } from './LoginForm';

test('renders form components', () => {
  render(<LoginForm onSubmit={() => {}} />);
  expect(screen.getByText('Submit')).toBeInTheDocument();
});
""")

    (dir_path / "src" / "services" / "authService.js").write_text("""import axios from 'axios';

export const authService = {
  async login(credentials) {
    const res = await axios.post('/api/login', credentials);
    return res.data;
  }
};
""")

def create_small_angular_project(dir_path: Path):
    os.makedirs(dir_path / "src" / "app", exist_ok=True)

    (dir_path / "package.json").write_text(json.dumps({
        "name": "small-angular-app",
        "version": "1.0.0",
        "dependencies": {
            "@angular/core": "^17.0.0",
            "@angular/common": "^17.0.0"
        }
    }))

    (dir_path / "angular.json").write_text(json.dumps({"$schema": "./node_modules/@angular/cli/lib/config/schema.json"}))

    (dir_path / "src" / "app" / "simple.component.ts").write_text("""import { Component } from '@angular/core';

@Component({
  selector: 'app-simple',
  template: '<p>Simple Angular Component</p>'
})
export class SimpleComponent {}
""")

def create_large_angular_project(dir_path: Path):
    os.makedirs(dir_path / "src" / "app" / "login", exist_ok=True)
    os.makedirs(dir_path / "src" / "app" / "dashboard", exist_ok=True)
    os.makedirs(dir_path / "src" / "app" / "services", exist_ok=True)
    os.makedirs(dir_path / "src" / "app" / "guards", exist_ok=True)

    (dir_path / "package.json").write_text(json.dumps({
        "name": "large-angular-app",
        "version": "2.0.0",
        "dependencies": {
            "@angular/core": "^17.0.0",
            "@angular/common": "^17.0.0",
            "@angular/forms": "^17.0.0",
            "@angular/router": "^17.0.0"
        }
    }))

    (dir_path / "angular.json").write_text(json.dumps({"$schema": "./node_modules/@angular/cli/lib/config/schema.json"}))

if __name__ == "__main__":
    react_small = SCRATCH_DIR / "react_small"
    react_large = SCRATCH_DIR / "react_large"
    angular_small = SCRATCH_DIR / "angular_small"
    angular_large = SCRATCH_DIR / "angular_large"

    shutil.rmtree(react_small, ignore_errors=True)
    shutil.rmtree(react_large, ignore_errors=True)
    shutil.rmtree(angular_small, ignore_errors=True)
    shutil.rmtree(angular_large, ignore_errors=True)

    create_small_react_project(react_small)
    create_large_react_project(react_large)
    create_small_angular_project(angular_small)
    create_large_angular_project(angular_large)
    print("Successfully generated all mock project workspaces!")
