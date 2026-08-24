import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  ListChecks,
  Plus,
  Search,
  Filter,
  Home,
  Settings,
  RotateCcw,
  Check,
  X,
  Trash2,
  Edit2,
  Clock,
  AlertCircle,
  User as UserIcon,
  Lock,
  Mail,
  ArrowRight
} from 'lucide-react';
import {
  fetchTasks,
  createTask,
  updateTask,
  toggleTaskComplete,
  deleteTask,
  fetchDashboard,
  loginUser,
  registerUser,
  Task,
  DashboardSummary
} from './api';

export default function App() {
  const [currentUser, setCurrentUser] = useState<{ name: string; email: string } | null>({
    name: 'Demo User',
    email: 'user@todoapp.com'
  });
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [loginEmail, setLoginEmail] = useState('user@todoapp.com');
  const [loginPass, setLoginPass] = useState('password123');
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPass, setRegPass] = useState('');
  const [authError, setAuthError] = useState('');

  const [activeTab, setActiveTab] = useState<'dashboard' | 'tasks' | 'create' | 'settings'>('dashboard');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [tasks, setTasks] = useState<Task[]>([]);
  const [dashboard, setDashboard] = useState<DashboardSummary>({
    total: 0,
    completed: 0,
    in_progress: 0,
    pending: 0,
    overdue: 0,
    recent_tasks: []
  });
  const [loading, setLoading] = useState<boolean>(true);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  // Form states
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDesc, setTaskDesc] = useState('');
  const [taskDueDate, setTaskDueDate] = useState('');
  const [taskPriority, setTaskPriority] = useState('Medium');

  useEffect(() => {
    loadData();
  }, [statusFilter, searchQuery]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tList, dData] = await Promise.all([
        fetchTasks(statusFilter, searchQuery),
        fetchDashboard()
      ]);
      setTasks(tList);
      setDashboard(dData);
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    try {
      const res = await loginUser(loginEmail, loginPass);
      setCurrentUser(res.user || { name: loginEmail.split('@')[0], email: loginEmail });
    } catch (err: any) {
      setAuthError(err.message || 'Login failed');
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    try {
      await registerUser(regName, regEmail, regPass);
      setCurrentUser({ name: regName, email: regEmail });
    } catch (err: any) {
      setAuthError(err.message || 'Registration failed');
    }
  };

  const handleCreateTaskSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle.trim()) return;
    try {
      await createTask({
        title: taskTitle,
        description: taskDesc,
        due_date: taskDueDate,
        priority: taskPriority
      });
      resetForm();
      setShowCreateModal(false);
      loadData();
    } catch (err) {
      console.error('Create task error:', err);
    }
  };

  const handleEditTaskSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTask || !taskTitle.trim()) return;
    try {
      await updateTask(editingTask.id, {
        title: taskTitle,
        description: taskDesc,
        due_date: taskDueDate,
        priority: taskPriority
      });
      resetForm();
      setEditingTask(null);
      loadData();
    } catch (err) {
      console.error('Edit task error:', err);
    }
  };

  const handleToggleComplete = async (t: Task) => {
    try {
      await toggleTaskComplete(t.id, !t.completed);
      loadData();
    } catch (err) {
      console.error('Toggle complete error:', err);
    }
  };

  const handleDeleteTask = async (id: string) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
      await deleteTask(id);
      loadData();
    } catch (err) {
      console.error('Delete task error:', err);
    }
  };

  const openEditModal = (t: Task) => {
    setEditingTask(t);
    setTaskTitle(t.title);
    setTaskDesc(t.description || '');
    setTaskDueDate(t.due_date || '');
    setTaskPriority(t.priority || 'Medium');
  };

  const resetForm = () => {
    setTaskTitle('');
    setTaskDesc('');
    setTaskDueDate('');
    setTaskPriority('Medium');
  };

  // If user is logged out
  if (!currentUser) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800 border border-slate-700 rounded-3xl max-w-md w-full p-8 shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center mx-auto text-white shadow-lg">
              <CheckCircle2 size={24} />
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">TodoApp</h2>
            <p className="text-xs text-slate-400">Integrated Application Live Environment</p>
          </div>

          {authError && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs p-3 rounded-xl flex items-center gap-2">
              <AlertCircle size={16} />
              <span>{authError}</span>
            </div>
          )}

          {authView === 'login' ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Email</label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500"
                    placeholder="user@todoapp.com"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Password</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={loginPass}
                    onChange={(e) => setLoginPass(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 rounded-xl transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Log In</span>
                <ArrowRight size={16} />
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => { setAuthView('register'); setAuthError(''); }}
                  className="text-xs text-slate-400 hover:text-emerald-400"
                >
                  Don't have an account? <strong className="text-emerald-400">Register</strong>
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Full Name</label>
                <div className="relative">
                  <UserIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    required
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500"
                    placeholder="John Doe"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Email</label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500"
                    placeholder="john@example.com"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Password</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={regPass}
                    onChange={(e) => setRegPass(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500"
                    placeholder="Min 8 characters"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 rounded-xl transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Create Account</span>
                <ArrowRight size={16} />
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => { setAuthView('login'); setAuthError(''); }}
                  className="text-xs text-slate-400 hover:text-emerald-400"
                >
                  Already have an account? <strong className="text-emerald-400">Log In</strong>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden text-slate-800 font-sans">
      {/* Navigation Sidebar */}
      <aside className="w-56 bg-[#0f172a] text-white flex flex-col shrink-0 p-4 justify-between">
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-md">
                <CheckCircle2 size={18} />
              </div>
              <span className="font-extrabold text-base tracking-wider">TodoApp</span>
            </div>
          </div>

          <nav className="space-y-1 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors cursor-pointer ${
                activeTab === 'dashboard' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
              }`}
            >
              <Home size={16} />
              <span>Dashboard</span>
            </button>

            <button
              onClick={() => setActiveTab('tasks')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors cursor-pointer ${
                activeTab === 'tasks' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
              }`}
            >
              <ListChecks size={16} />
              <span>My Tasks ({tasks.length})</span>
            </button>

            <button
              onClick={() => { resetForm(); setShowCreateModal(true); }}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-slate-300 hover:bg-slate-800/60 hover:text-white rounded-xl transition-colors cursor-pointer"
            >
              <Plus size={16} />
              <span>Create Task</span>
            </button>

            <button
              onClick={() => setActiveTab('settings')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors cursor-pointer ${
                activeTab === 'settings' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
              }`}
            >
              <Settings size={16} />
              <span>Settings</span>
            </button>
          </nav>
        </div>

        {/* User profile & Logout */}
        <div className="pt-4 border-t border-slate-800 space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 font-bold text-xs flex items-center justify-center border border-emerald-500/30 shrink-0">
              {currentUser.name.charAt(0)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-white truncate">{currentUser.name}</p>
              <p className="text-[10px] text-slate-400 truncate">{currentUser.email}</p>
            </div>
          </div>

          <button
            onClick={() => setCurrentUser(null)}
            className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-red-400 transition-colors w-full px-2 py-1.5 cursor-pointer"
          >
            <RotateCcw size={14} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto bg-slate-50 p-6 space-y-6">
        {/* Top Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
              {activeTab === 'dashboard' && 'Dashboard'}
              {activeTab === 'tasks' && 'My Tasks'}
              {activeTab === 'settings' && 'Settings'}
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Welcome back, {currentUser.name}! Here is your task environment.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Search Input */}
            <div className="relative w-64">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search tasks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500 shadow-2xs"
              />
            </div>

            <button
              onClick={() => { resetForm(); setShowCreateModal(true); }}
              className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3.5 py-1.5 rounded-xl flex items-center gap-1.5 transition-all shadow-sm cursor-pointer"
            >
              <Plus size={14} />
              <span>New Task</span>
            </button>
          </div>
        </div>

        {/* View: DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* 4 Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-2xs flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500">Total Tasks</span>
                  <h4 className="text-2xl font-black text-slate-900 mt-1">{dashboard.total}</h4>
                  <span className="text-[10px] font-bold text-emerald-600 mt-0.5 block">Active system total</span>
                </div>
                <div className="w-11 h-11 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100 shadow-2xs">
                  <ListChecks size={20} />
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-2xs flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500">Completed</span>
                  <h4 className="text-2xl font-black text-slate-900 mt-1">{dashboard.completed}</h4>
                  <span className="text-[10px] font-medium text-slate-400 mt-0.5 block">
                    {dashboard.total > 0 ? Math.round((dashboard.completed / dashboard.total) * 100) : 0}% done
                  </span>
                </div>
                <div className="w-11 h-11 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100 shadow-2xs">
                  <CheckCircle2 size={20} />
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-2xs flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500">In Progress</span>
                  <h4 className="text-2xl font-black text-slate-900 mt-1">{dashboard.in_progress}</h4>
                  <span className="text-[10px] font-medium text-slate-400 mt-0.5 block">Active work</span>
                </div>
                <div className="w-11 h-11 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100 shadow-2xs">
                  <Clock size={20} />
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-2xs flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500">Overdue</span>
                  <h4 className="text-2xl font-black text-slate-900 mt-1">{dashboard.overdue}</h4>
                  <span className="text-[10px] font-bold text-red-500 mt-0.5 block">Needs attention</span>
                </div>
                <div className="w-11 h-11 rounded-2xl bg-red-50 text-red-500 flex items-center justify-center border border-red-100 shadow-2xs">
                  <AlertCircle size={20} />
                </div>
              </div>
            </div>

            {/* Task Table in Dashboard */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-2xs space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-900">Task Overview</h4>
                <button
                  onClick={() => setActiveTab('tasks')}
                  className="text-xs font-bold text-emerald-600 hover:text-emerald-700 cursor-pointer"
                >
                  View All Tasks &rarr;
                </button>
              </div>

              {renderTaskTable(tasks.slice(0, 5))}
            </div>
          </div>
        )}

        {/* View: TASKS */}
        {activeTab === 'tasks' && (
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-2xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-700">Filter:</span>
                {['All', 'Pending', 'In Progress', 'Completed'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`text-xs font-bold px-3 py-1 rounded-xl transition-all cursor-pointer ${
                      statusFilter === st
                        ? 'bg-emerald-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            {renderTaskTable(tasks)}
          </div>
        )}

        {/* View: SETTINGS */}
        {activeTab === 'settings' && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs max-w-xl space-y-4">
            <h4 className="text-sm font-bold text-slate-900">Application Configuration</h4>
            <div className="text-xs space-y-2 text-slate-600">
              <p><strong>Environment:</strong> Integrated Project Merge Preview</p>
              <p><strong>Frontend Port:</strong> 5175</p>
              <p><strong>Backend Port:</strong> 8010</p>
              <p><strong>Backend API Status:</strong> <span className="text-emerald-600 font-bold">Healthy</span></p>
            </div>
          </div>
        )}
      </main>

      {/* CREATE / EDIT TASK MODAL */}
      {(showCreateModal || editingTask) && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white border border-slate-200 rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                {editingTask ? 'Edit Task' : 'Create New Task'}
              </h3>
              <button
                onClick={() => { setShowCreateModal(false); setEditingTask(null); }}
                className="text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={editingTask ? handleEditTaskSubmit : handleCreateTaskSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Task Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Complete story verification"
                  value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Description</label>
                <textarea
                  rows={3}
                  placeholder="Task details..."
                  value={taskDesc}
                  onChange={(e) => setTaskDesc(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Due Date</label>
                  <input
                    type="date"
                    value={taskDueDate}
                    onChange={(e) => setTaskDueDate(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Priority</label>
                  <select
                    value={taskPriority}
                    onChange={(e) => setTaskPriority(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { setShowCreateModal(false); setEditingTask(null); }}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl font-bold hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-sm cursor-pointer"
                >
                  {editingTask ? 'Save Changes' : 'Create Task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );

  function renderTaskTable(taskList: Task[]) {
    if (taskList.length === 0) {
      return (
        <div className="text-center py-8 text-slate-400 text-xs">
          No tasks found matching your criteria.
        </div>
      );
    }

    return (
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase">
              <th className="py-2.5 px-3">Task</th>
              <th className="py-2.5 px-3">Priority</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">Due Date</th>
              <th className="py-2.5 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {taskList.map((t) => (
              <tr key={t.id} className="hover:bg-slate-50/50">
                <td className="py-3 px-3 font-medium text-slate-900 flex items-center gap-2.5">
                  <button
                    onClick={() => handleToggleComplete(t)}
                    className={`w-5 h-5 rounded border flex items-center justify-center cursor-pointer transition-colors ${
                      t.completed
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-600'
                        : 'border-slate-300 bg-white hover:border-slate-400'
                    }`}
                  >
                    {t.completed && <Check size={12} />}
                  </button>
                  <span className={t.completed ? 'line-through text-slate-400' : 'font-bold text-slate-800'}>
                    {t.title}
                  </span>
                </td>
                <td className="py-3 px-3">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                    t.priority === 'High' ? 'bg-red-50 text-red-700 border-red-200' :
                    t.priority === 'Medium' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                    'bg-blue-50 text-blue-700 border-blue-200'
                  }`}>
                    {t.priority || 'Medium'}
                  </span>
                </td>
                <td className="py-3 px-3">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                    t.completed || t.status === 'Completed' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                    t.status === 'In Progress' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                    'bg-slate-100 text-slate-600 border-slate-200'
                  }`}>
                    {t.status || (t.completed ? 'Completed' : 'Pending')}
                  </span>
                </td>
                <td className="py-3 px-3 text-slate-500">
                  {t.due_date || 'No date'}
                </td>
                <td className="py-3 px-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => openEditModal(t)}
                      className="p-1 text-slate-400 hover:text-slate-600 rounded cursor-pointer"
                      title="Edit Task"
                    >
                      <Edit2 size={13} />
                    </button>
                    <button
                      onClick={() => handleDeleteTask(t.id)}
                      className="p-1 text-slate-400 hover:text-red-600 rounded cursor-pointer"
                      title="Delete Task"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
}
