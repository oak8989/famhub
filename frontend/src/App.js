import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Toaster } from './components/ui/sonner';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import CalendarPage from './pages/CalendarPage';
import ShoppingPage from './pages/ShoppingPage';
import TasksPage from './pages/TasksPage';
import NotesPage from './pages/NotesPage';
import BudgetPage from './pages/BudgetPage';
import MealPlannerPage from './pages/MealPlannerPage';
import RecipesPage from './pages/RecipesPage';
import GroceryPage from './pages/GroceryPage';
import ContactsPage from './pages/ContactsPage';
import PantryPage from './pages/PantryPage';
import SuggestionsPage from './pages/SuggestionsPage';
import ChoresPage from './pages/ChoresPage';
import SettingsPage from './pages/SettingsPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import Layout from './components/Layout';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  return children;
};

const ModuleRoute = ({ moduleKey, children }) => {
  const { isModuleVisible } = useAuth();
  if (moduleKey && !isModuleVisible(moduleKey)) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

const AppRoutes = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <AuthPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
      <Route path="/calendar" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="calendar"><CalendarPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/shopping" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="shopping"><ShoppingPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/tasks" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="tasks"><TasksPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/notes" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="notes"><NotesPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/budget" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="budget"><BudgetPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/meals" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="meals"><MealPlannerPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/recipes" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="recipes"><RecipesPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/grocery" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="grocery"><GroceryPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/contacts" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="contacts"><ContactsPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/pantry" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="pantry"><PantryPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/suggestions" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="suggestions"><SuggestionsPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/chores" element={<ProtectedRoute><Layout><ModuleRoute moduleKey="chores"><ChoresPage /></ModuleRoute></Layout></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><Layout><SettingsPage /></Layout></ProtectedRoute>} />
    </Routes>
  );
};

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
          <Toaster position="top-right" richColors />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
