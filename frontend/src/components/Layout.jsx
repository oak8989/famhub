import React, { useState, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import useWebSocket from '../lib/useWebSocket';
import {
  Home, CalendarDays, ShoppingCart, CheckSquare, StickyNote,
  DollarSign, UtensilsCrossed, BookOpen, ListOrdered, Contact,
  Package, Lightbulb, Award, Settings, LogOut, Menu, X, Sun, Moon
} from 'lucide-react';
import { toast } from 'sonner';

const navItems = [
  { path: '/dashboard', icon: Home, label: 'Home' },
  { path: '/calendar', icon: CalendarDays, label: 'Calendar' },
  { path: '/shopping', icon: ShoppingCart, label: 'Shopping' },
  { path: '/tasks', icon: CheckSquare, label: 'Tasks' },
  { path: '/chores', icon: Award, label: 'Chores' },
  { path: '/notes', icon: StickyNote, label: 'Notes' },
  { path: '/budget', icon: DollarSign, label: 'Budget' },
  { path: '/meals', icon: UtensilsCrossed, label: 'Meals' },
  { path: '/recipes', icon: BookOpen, label: 'Recipes' },
  { path: '/grocery', icon: ListOrdered, label: 'Grocery' },
  { path: '/contacts', icon: Contact, label: 'Contacts' },
  { path: '/pantry', icon: Package, label: 'Pantry' },
  { path: '/suggestions', icon: Lightbulb, label: 'Ideas' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

const Layout = ({ children }) => {
  const { user, family, logout, isModuleVisible } = useAuth();
  const { darkMode, toggleDarkMode } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Module key mapping: path segment → settings key
  const moduleKeyMap = {
    '/calendar': 'calendar',
    '/shopping': 'shopping',
    '/tasks': 'tasks',
    '/notes': 'notes',
    '/budget': 'budget',
    '/meals': 'meals',
    '/recipes': 'recipes',
    '/grocery': 'grocery',
    '/contacts': 'contacts',
    '/pantry': 'pantry',
    '/suggestions': 'suggestions',
    '/chores': 'chores',
  };

  const visibleNavItems = navItems.filter((item) => {
    const moduleKey = moduleKeyMap[item.path];
    if (!moduleKey) return true; // dashboard, settings always visible
    return isModuleVisible(moduleKey);
  });

  const handleWSMessage = useCallback((msg) => {
    if (msg.type === 'update') {
      toast.info(`${msg.module} was updated by a family member`, { duration: 3000 });
      // Dispatch custom event for pages to listen to
      window.dispatchEvent(new CustomEvent('ws-update', { detail: msg }));
    }
  }, []);

  useWebSocket(user?.family_id, handleWSMessage);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="flex h-screen bg-background dark:bg-gray-900 transition-colors" data-testid="app-layout">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-64 bg-warm-white dark:bg-gray-800 border-r border-sunny/30 dark:border-gray-700 transition-colors">
        <div className="p-6 border-b border-sunny/30 dark:border-gray-700">
          <h1 className="text-2xl font-heading font-bold text-terracotta">Family Hub</h1>
          {family && <p className="text-sm text-navy-light dark:text-gray-400 font-handwritten text-lg">{family.name}</p>}
        </div>

        <nav className="flex-1 overflow-y-auto p-3">
          <ul className="space-y-1">
            {visibleNavItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-terracotta text-white shadow-warm'
                        : 'text-navy dark:text-gray-300 hover:bg-cream dark:hover:bg-gray-700'
                    }`}
                    data-testid={`nav-${item.label.toLowerCase()}`}
                  >
                    <item.icon className="w-5 h-5" />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="p-4 border-t border-sunny/30 dark:border-gray-700 space-y-2">
          <button
            onClick={toggleDarkMode}
            className="flex items-center gap-3 w-full px-4 py-2 rounded-xl text-sm text-navy dark:text-gray-300 hover:bg-cream dark:hover:bg-gray-700 transition-colors"
            data-testid="dark-mode-toggle"
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </button>
          <div className="flex items-center gap-3 px-4 py-2 text-sm">
            <div className="w-8 h-8 rounded-full bg-terracotta text-white flex items-center justify-center text-sm font-bold">
              {user?.name?.charAt(0) || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-navy dark:text-gray-200 truncate">{user?.name}</p>
              <p className="text-xs text-navy-light dark:text-gray-400 capitalize">{user?.role}</p>
            </div>
            <button onClick={handleLogout} className="text-navy-light dark:text-gray-400 hover:text-red-500" data-testid="logout-btn">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile Header & Menu */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="lg:hidden sticky top-0 z-40 flex items-center justify-between px-4 py-3 bg-warm-white dark:bg-gray-800 border-b border-sunny/30 dark:border-gray-700 transition-colors" style={{ paddingTop: 'max(0.75rem, env(safe-area-inset-top))' }}>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-navy dark:text-gray-300 p-2 -ml-2 rounded-lg active:bg-cream dark:active:bg-gray-700"
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
            <h1 className="text-xl font-heading font-bold text-terracotta">Family Hub</h1>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={toggleDarkMode}
              className="text-navy dark:text-gray-300 p-3 rounded-lg hover:bg-cream dark:hover:bg-gray-700 active:bg-cream/80 dark:active:bg-gray-600"
              data-testid="mobile-dark-mode-toggle"
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <button
              onClick={handleLogout}
              className="text-navy-light dark:text-gray-400 p-3 rounded-lg hover:bg-cream dark:hover:bg-gray-700 active:bg-red-50 dark:active:bg-red-900/30"
              data-testid="mobile-logout-btn"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Mobile Nav Overlay */}
        {mobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-50 bg-black/50" onClick={() => setMobileMenuOpen(false)}>
            <div className="w-72 h-full bg-warm-white dark:bg-gray-800 p-4 overflow-y-auto transition-colors" onClick={e => e.stopPropagation()}>
              <div className="mb-4 pb-3 border-b border-sunny/30 dark:border-gray-700">
                <h2 className="font-heading font-bold text-terracotta text-xl">Family Hub</h2>
                {family && <p className="text-sm text-navy-light dark:text-gray-400 font-handwritten">{family.name}</p>}
              </div>
              <ul className="space-y-1">
                {visibleNavItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                          isActive
                            ? 'bg-terracotta text-white'
                            : 'text-navy dark:text-gray-300 hover:bg-cream dark:hover:bg-gray-700'
                        }`}
                      >
                        <item.icon className="w-5 h-5" />
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-background dark:bg-gray-900 transition-colors">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
