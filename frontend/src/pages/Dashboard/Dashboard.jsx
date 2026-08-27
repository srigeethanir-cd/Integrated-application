import React, { useState } from 'react';
import './Dashboard.css';

export default function Dashboard({ projects = [], onCreateNew, onOpenProject, onDeleteProject }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [frameworkFilter, setFrameworkFilter] = useState('all');

    const filteredProjects = projects.filter((project) => {
        const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesFramework = frameworkFilter === 'all' || project.framework === frameworkFilter;
        return matchesSearch && matchesFramework;
    });

    const getFrameworkBadge = (framework) => {
        switch (framework) {
            case 'react-js':
                return { label: 'React JS', color: '#61dafb', bg: 'rgba(97, 218, 251, 0.12)' };
            case 'react-ts':
                return { label: 'React TS', color: '#3178c6', bg: 'rgba(49, 120, 198, 0.12)' };
            case 'angular':
                return { label: 'Angular', color: '#dd0031', bg: 'rgba(221, 0, 49, 0.12)' };
            default:
                return { label: framework || 'Web', color: '#7b4dff', bg: 'rgba(123, 77, 255, 0.12)' };
        }
    };

    const getCssBadge = (cssFramework) => {
        switch (cssFramework) {
            case 'tailwind':
                return { label: 'Tailwind CSS', color: '#38bdf8' };
            case 'bootstrap':
                return { label: 'Bootstrap 5', color: '#7952b3' };
            case 'mui':
                return { label: 'Material UI', color: '#007fff' };
            default:
                return { label: cssFramework || 'CSS', color: '#687089' };
        }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return 'Recently created';
        try {
            return new Date(dateStr).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch {
            return 'Recently created';
        }
    };

    return (
        <div className="dashboard-container">
            {/* Header Section */}
            <div className="dashboard-header">
                <div>
                    <h1 className="dashboard-title">Projects & Workspaces</h1>
                    <p className="dashboard-subtitle">
                        Manage your UI projects, ingest user stories & wireframes, and generate code seamlessly.
                    </p>
                </div>
                <button className="create-project-btn" onClick={onCreateNew}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="12" y1="5" x2="12" y2="19"></line>
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    Create New Project
                </button>
            </div>

            {/* Controls / Filter Bar */}
            <div className="dashboard-controls">
                <div className="search-box">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                    <input
                        type="text"
                        placeholder="Search projects by name..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    {searchQuery && (
                        <button className="clear-search" onClick={() => setSearchQuery('')}>×</button>
                    )}
                </div>

                <div className="filter-group">
                    <label htmlFor="frameworkFilter">Framework:</label>
                    <select
                        id="frameworkFilter"
                        value={frameworkFilter}
                        onChange={(e) => setFrameworkFilter(e.target.value)}
                    >
                        <option value="all">All Frameworks</option>
                        <option value="react-js">React JS</option>
                        <option value="react-ts">React TS</option>
                        <option value="angular">Angular</option>
                    </select>
                </div>
            </div>

            {/* Projects Grid */}
            {filteredProjects.length > 0 ? (
                <div className="dashboard-grid">
                    {filteredProjects.map((project) => {
                        const fwBadge = getFrameworkBadge(project.framework);
                        const cssBadge = getCssBadge(project.cssFramework);

                        return (
                            <div
                                key={project.id}
                                className="dashboard-card"
                                onClick={() => onOpenProject(project)}
                            >
                                <div className="card-top">
                                    <div className="card-icon" style={{ background: fwBadge.bg, color: fwBadge.color }}>
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                                        </svg>
                                    </div>
                                    <button
                                        className="delete-card-btn"
                                        title="Delete Project"
                                        onClick={(e) => onDeleteProject(project.id, project.name, e)}
                                    >
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polyline points="3 6 5 6 21 6"></polyline>
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                        </svg>
                                    </button>
                                </div>

                                <div className="card-body">
                                    <h3 className="project-title">{project.name}</h3>
                                    <div className="project-badges">
                                        <span className="badge fw-badge" style={{ color: fwBadge.color, borderColor: `${fwBadge.color}33`, background: fwBadge.bg }}>
                                            {fwBadge.label}
                                        </span>
                                        <span className="badge css-badge">
                                            {cssBadge.label}
                                        </span>
                                    </div>
                                </div>

                                <div className="card-footer">
                                    <span className="project-date">Created {formatDate(project.createdAt)}</span>
                                    <span className="open-link">
                                        Open
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                            <line x1="5" y1="12" x2="19" y2="12"></line>
                                            <polyline points="12 5 19 12 12 19"></polyline>
                                        </svg>
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                <div className="empty-state">
                    <div className="empty-icon">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                            <line x1="12" y1="11" x2="12" y2="17"></line>
                            <line x1="9" y1="14" x2="15" y2="14"></line>
                        </svg>
                    </div>
                    {projects.length === 0 ? (
                        <>
                            <h3>No Projects Yet</h3>
                            <p>Get started by creating your first project to ingest user stories and generate React or Angular code.</p>
                            <button className="create-project-btn" onClick={onCreateNew}>
                                Create First Project
                            </button>
                        </>
                    ) : (
                        <>
                            <h3>No Matching Projects Found</h3>
                            <p>Try adjusting your search query or framework filter.</p>
                            <button className="clear-filter-btn" onClick={() => { setSearchQuery(''); setFrameworkFilter('all'); }}>
                                Reset Filters
                            </button>
                        </>
                    )}
                </div>
            )}
        </div>
    );
}
