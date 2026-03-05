import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Calendar, ShoppingCart, CheckSquare, FileText,
  DollarSign, Utensils, BookOpen, List, Users, Package, Lightbulb,
  ArrowRight, Award, Settings
} from 'lucide-react';
import { calendarAPI, tasksAPI, shoppingAPI, budgetAPI, notesAPI, choresAPI } from '../lib/api';

const modules = [
  { path: '/calendar', icon: Calendar, label: 'Calendar', color: 'bg-terracotta', desc: 'Family events' },
  { path: '/shopping', icon: ShoppingCart, label: 'Shopping', color: 'bg-sage', desc: 'Shared list' },
  { path: '/tasks', icon: CheckSquare, label: 'Tasks', color: 'bg-sunny', desc: 'To-dos' },
  { path: '/chores', icon: Award, label: 'Chores', color: 'bg-purple-400', desc: 'Earn rewards' },
  { path: '/notes', icon: FileText, label: 'Notes', color: 'bg-blue-400', desc: 'Shared notes' },
  { path: '/budget', icon: DollarSign, label: 'Budget', color: 'bg-green-500', desc: 'Track finances' },
  { path: '/meals', icon: Utensils, label: 'Meals', color: 'bg-orange-400', desc: 'Plan meals' },
  { path: '/recipes', icon: BookOpen, label: 'Recipes', color: 'bg-pink-400', desc: 'Recipe box' },
  { path: '/grocery', icon: List, label: 'Grocery', color: 'bg-teal-400', desc: 'Quick list' },
  { path: '/contacts', icon: Users, label: 'Contacts', color: 'bg-indigo-400', desc: 'Address book' },
  { path: '/pantry', icon: Package, label: 'Pantry', color: 'bg-amber-500', desc: 'Inventory' },
  { path: '/suggestions', icon: Lightbulb, label: 'Ideas', color: 'bg-cyan-500', desc: 'Meal ideas' },
  { path: '/settings', icon: Settings, label: 'Settings', color: 'bg-gray-500', desc: 'Manage family' },
];

const Dashboard = () => {
  const { user, family } = useAuth();
  const [stats, setStats] = useState({
    events: 0,
    tasks: 0,
    shopping: 0,
    balance: 0,
    chores: 0,
    points: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [eventsRes, tasksRes, shoppingRes, budgetRes, choresRes] = await Promise.all([
          calendarAPI.getEvents().catch(() => ({ data: [] })),
          tasksAPI.getTasks().catch(() => ({ data: [] })),
          shoppingAPI.getItems().catch(() => ({ data: [] })),
          budgetAPI.getSummary().catch(() => ({ data: { balance: 0 } })),
          choresAPI.getChores().catch(() => ({ data: [] }))
        ]);

        setStats({
          events: eventsRes.data?.length || 0,
          tasks: tasksRes.data?.filter(t => !t.completed)?.length || 0,
          shopping: shoppingRes.data?.filter(i => !i.checked)?.length || 0,
          balance: budgetRes.data?.balance || 0,
          chores: choresRes.data?.filter(c => !c.completed)?.length || 0,
          points: user?.points || 0
        });
      } catch (error) {
        console.error('Failed to load stats:', error);
      }
      setLoading(false);
    };

    loadStats();
  }, [user?.points]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="space-y-8" data-testid="dashboard">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-heading font-bold text-navy">
            {getGreeting()}, {user?.name?.split(' ')[0] || 'Friend'}!
          </h1>
          <p className="text-navy-light mt-1 font-handwritten text-xl">
            Welcome to {family?.name || 'your Family Hub'}
          </p>
        </div>
        {user?.points > 0 && (
          <div className="flex items-center gap-2 bg-sunny/20 px-4 py-2 rounded-xl">
            <Award className="w-5 h-5 text-amber-500" />
            <span className="font-bold text-navy">{user.points} points</span>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link to="/calendar" className="module-card card-hover" data-testid="stat-events">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-terracotta/10 rounded-xl flex items-center justify-center">
              <Calendar className="w-6 h-6 text-terracotta" />
            </div>
            <div>
              <p className="text-2xl font-heading font-bold text-navy">
                {loading ? '...' : stats.events}
              </p>
              <p className="text-sm text-navy-light">Events</p>
            </div>
          </div>
        </Link>

        <Link to="/tasks" className="module-card card-hover" data-testid="stat-tasks">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-sunny/20 rounded-xl flex items-center justify-center">
              <CheckSquare className="w-6 h-6 text-sunny" />
            </div>
            <div>
              <p className="text-2xl font-heading font-bold text-navy">
                {loading ? '...' : stats.tasks}
              </p>
              <p className="text-sm text-navy-light">Tasks</p>
            </div>
          </div>
        </Link>

        <Link to="/chores" className="module-card card-hover" data-testid="stat-chores">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <Award className="w-6 h-6 text-purple-500" />
            </div>
            <div>
              <p className="text-2xl font-heading font-bold text-navy">
                {loading ? '...' : stats.chores}
              </p>
              <p className="text-sm text-navy-light">Chores</p>
            </div>
          </div>
        </Link>

        <Link to="/budget" className="module-card card-hover" data-testid="stat-balance">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              stats.balance >= 0 ? 'bg-green-100' : 'bg-red-100'
            }`}>
              <DollarSign className={`w-6 h-6 ${stats.balance >= 0 ? 'text-green-500' : 'text-red-500'}`} />
            </div>
            <div>
              <p className={`text-2xl font-heading font-bold ${
                stats.balance >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {loading ? '...' : `$${Math.abs(stats.balance).toFixed(0)}`}
              </p>
              <p className="text-sm text-navy-light">Balance</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="card-cozy">
        <h2 className="text-lg font-heading font-bold text-navy mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link to="/calendar" className="btn-outline flex items-center gap-2 text-sm">
            <Calendar className="w-4 h-4" /> Add Event
          </Link>
          <Link to="/tasks" className="btn-outline flex items-center gap-2 text-sm">
            <CheckSquare className="w-4 h-4" /> New Task
          </Link>
          <Link to="/shopping" className="btn-outline flex items-center gap-2 text-sm">
            <ShoppingCart className="w-4 h-4" /> Shopping List
          </Link>
          <Link to="/chores" className="btn-outline flex items-center gap-2 text-sm">
            <Award className="w-4 h-4" /> View Chores
          </Link>
        </div>
      </div>

      {/* Module Grid */}
      <div>
        <h2 className="text-lg font-heading font-bold text-navy mb-4">All Modules</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {modules.map((module) => {
            const Icon = module.icon;
            return (
              <Link
                key={module.path}
                to={module.path}
                className="module-card card-hover group"
                data-testid={`module-${module.label.toLowerCase()}`}
              >
                <div className={`w-12 h-12 ${module.color} rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-medium text-navy">{module.label}</h3>
                <p className="text-xs text-navy-light">{module.desc}</p>
                <ArrowRight className="w-4 h-4 text-navy-light absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
