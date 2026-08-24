typescript
// ProjectBlueprint.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ProjectBlueprint {
  architecture: string;
  modules: string[];
  api: string;
  databaseSchema: string;
}

interface UserStory {
  id: number;
  description: string;
  approved: boolean;
}

const ProjectBlueprintComponent = () => {
  const [userStories, setUserStories] = useState<UserStory[]>([]);
  const [projectBlueprint, setProjectBlueprint] = useState<ProjectBlueprint>({
    architecture: '',
    modules: [],
    api: '',
    databaseSchema: '',
  });

  useEffect(() => {
    const fetchUserStories = async () => {
      try {
        const response = await axios.get('http://localhost:8000/user-stories');
        const approvedUserStories = response.data.filter((story: UserStory) => story.approved);
        setUserStories(approvedUserStories);
      } catch (error) {
        console.error(error);
      }
    };
    fetchUserStories();
  }, []);

  const generateProjectBlueprint = async () => {
    try {
      const response = await axios.post('http://localhost:8000/project-blueprint', {
        userStories,
      });
      setProjectBlueprint(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleGenerateBlueprint = () => {
    generateProjectBlueprint();
  };

  return (
    <div>
      <h1>Project Blueprint</h1>
      <button onClick={handleGenerateBlueprint}>Generate Blueprint</button>
      {projectBlueprint.architecture && (
        <div>
          <h2>Architecture Blueprint</h2>
          <p>{projectBlueprint.architecture}</p>
        </div>
      )}
      {projectBlueprint.modules.length > 0 && (
        <div>
          <h2>Required Modules</h2>
          <ul>
            {projectBlueprint.modules.map((module, index) => (
              <li key={index}>{module}</li>
            ))}
          </ul>
        </div>
      )}
      {projectBlueprint.api && (
        <div>
          <h2>API Blueprint</h2>
          <p>{projectBlueprint.api}</p>
        </div>
      )}
      {projectBlueprint.databaseSchema && (
        <div>
          <h2>Database Schema</h2>
          <p>{projectBlueprint.databaseSchema}</p>
        </div>
      )}
    </div>
  );
};

export default ProjectBlueprintComponent;