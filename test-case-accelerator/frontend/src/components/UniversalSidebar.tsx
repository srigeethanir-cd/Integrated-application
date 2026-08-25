import { 
  LayoutGrid, 
  Code2, 
  Terminal, 
  FileCheck2, 
  CheckSquare, 
  Settings as SettingsIcon, 
  Sparkles
} from 'lucide-react'

export function UniversalSidebar() {
  const activeAccelerator = 'Backend Unit-Testcase Generator';

  const menuItems = [
    { 
      label: 'User Story', 
      icon: LayoutGrid, 
      path: '/dashboard',
    },
    { 
      label: 'UI Code', 
      icon: Code2, 
      path: '/ui-code',
    },
    { 
      label: 'API Code', 
      icon: Terminal, 
      path: '/api-code',
    },
    { 
      label: 'Unit Test Cases', 
      icon: FileCheck2, 
      path: '/unit-test-cases/',
    },
    { 
      label: 'Application Testing', 
      icon: CheckSquare, 
      path: '/application-testing/',
    },
    { 
      label: 'Backend Unit-Testcase Generator', 
      icon: Sparkles, 
      path: '/backend-unit-testcase-generator/',
    },
  ];

  return (
    <aside 
      style={{
        width: '260px',
        height: '100vh',
        backgroundColor: '#1B1B3A',
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 30,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '24px 16px',
        boxSizing: 'border-box',
        borderRight: '1px solid rgba(45, 55, 72, 0.5)',
        userSelect: 'none',
        flexShrink: 0
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        {/* StoryForge AI Header */}
        <a href="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px', textDecoration: 'none' }}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '12px',
            background: 'linear-gradient(to right, #FF602B, #4318FF)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px rgba(67, 24, 255, 0.4)'
          }}>
            <Sparkles size={18} color="#ffffff" style={{ fill: '#ffffff' }} />
          </div>
          <span style={{
            fontSize: '18px',
            fontWeight: 800,
            color: '#ffffff',
            letterSpacing: '-0.025em',
            fontFamily: 'Inter, sans-serif'
          }}>
            StoryForge AI
          </span>
        </a>

        {/* Universal Sidebar Menu Items */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: 0 }}>
          {menuItems.map((item) => {
            const isActive = activeAccelerator === item.label;
            return (
              <a
                key={item.label}
                href={item.path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  borderRadius: '16px',
                  fontSize: '12px',
                  fontWeight: 700,
                  textDecoration: 'none',
                  transition: 'all 0.2s',
                  background: isActive ? 'linear-gradient(to right, #FF602B, #7551FF, #4318FF)' : 'transparent',
                  color: isActive ? '#ffffff' : '#A0AEC0',
                  boxShadow: isActive ? '0 6px 20px rgba(67, 24, 255, 0.35)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <item.icon size={16} color={isActive ? '#ffffff' : '#A0AEC0'} />
                  <span>{item.label}</span>
                </div>
                {isActive && (
                  <span style={{
                    width: '4px',
                    height: '16px',
                    backgroundColor: '#ffffff',
                    borderRadius: '9999px',
                    flexShrink: 0
                  }} />
                )}
              </a>
            );
          })}
        </nav>
      </div>

      {/* Bottom Settings & User Avatar ('N') */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <a
          href="/settings"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderRadius: '16px',
            fontSize: '12px',
            fontWeight: 700,
            color: '#A0AEC0',
            textDecoration: 'none',
            transition: 'all 0.2s'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <SettingsIcon size={16} color="#A0AEC0" />
            <span>Settings</span>
          </div>
        </a>

        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          backgroundColor: '#1A1A2E',
          border: '1px solid rgba(75, 85, 99, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ffffff',
          fontWeight: 800,
          fontSize: '12px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}>
          N
        </div>
      </div>
    </aside>
  );
}
