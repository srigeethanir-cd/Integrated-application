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

interface LayoutRule {
  id: number;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
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

interface Props {
  userStory: UserStory;
  layoutRules: LayoutRule[];
  colorsPalette: ColorsPalette;
  designTokens: DesignTokens;
}

const Dashboard: React.FC<Props> = ({
  userStory,
  layoutRules,
  colorsPalette,
  designTokens,
}) => {
  return (
    <div
      style={{
        backgroundColor: colorsPalette.background,
        height: '100vh',
        width: '100vw',
      }}
    >
      {layoutRules.map((rule) => {
        switch (rule.type) {
          case 'header':
            return (
              <div
                key={rule.id}
                style={{
                  position: 'absolute',
                  top: rule.y,
                  left: rule.x,
                  width: rule.width,
                  height: rule.height,
                  backgroundColor: colorsPalette.primary,
                  color: colorsPalette.text,
                  padding: designTokens.spacing.medium,
                  borderTopLeftRadius: designTokens.corners.small,
                  borderTopRightRadius: designTokens.corners.small,
                }}
              >
                {userStory.title}
              </div>
            );
          case 'hero_image':
            return (
              <div
                key={rule.id}
                style={{
                  position: 'absolute',
                  top: rule.y,
                  left: rule.x,
                  width: rule.width,
                  height: rule.height,
                  backgroundColor: colorsPalette.secondary,
                  padding: designTokens.spacing.medium,
                }}
              >
                <img
                  src="https://via.placeholder.com/375x200"
                  alt="Hero Image"
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    borderRadius: designTokens.corners.small,
                  }}
                />
              </div>
            );
          case 'text_block':
            return (
              <div
                key={rule.id}
                style={{
                  position: 'absolute',
                  top: rule.y,
                  left: rule.x,
                  width: rule.width,
                  height: rule.height,
                  backgroundColor: colorsPalette.background,
                  color: colorsPalette.text,
                  padding: designTokens.spacing.medium,
                }}
              >
                {userStory.description}
              </div>
            );
          case 'call_to_action':
            return (
              <button
                key={rule.id}
                style={{
                  position: 'absolute',
                  top: rule.y,
                  left: rule.x,
                  width: rule.width,
                  height: rule.height,
                  backgroundColor: colorsPalette.primary,
                  color: colorsPalette.text,
                  padding: designTokens.spacing.medium,
                  borderRadius: designTokens.corners.small,
                }}
              >
                View Tasks
              </button>
            );
          default:
            return null;
        }
      })}
    </div>
  );
};

export default Dashboard;