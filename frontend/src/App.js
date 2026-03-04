import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
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

const AppRoutes = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <AuthPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
      <Route path="/calendar" element={<ProtectedRoute><Layout><CalendarPage /></Layout></ProtectedRoute>} />
      <Route path="/shopping" element={<ProtectedRoute><Layout><ShoppingPage /></Layout></ProtectedRoute>} />
      <Route path="/tasks" element={<ProtectedRoute><Layout><TasksPage /></Layout></ProtectedRoute>} />
      <Route path="/notes" element={<ProtectedRoute><Layout><NotesPage /></Layout></ProtectedRoute>} />
      <Route path="/budget" element={<ProtectedRoute><Layout><BudgetPage /></Layout></ProtectedRoute>} />
      <Route path="/meals" element={<ProtectedRoute><Layout><MealPlannerPage /></Layout></ProtectedRoute>} />
      <Route path="/recipes" element={<ProtectedRoute><Layout><RecipesPage /></Layout></ProtectedRoute>} />
      <Route path="/grocery" element={<ProtectedRoute><Layout><GroceryPage /></Layout></ProtectedRoute>} />
      <Route path="/contacts" element={<ProtectedRoute><Layout><ContactsPage /></Layout></ProtectedRoute>} />
      <Route path="/pantry" element={<ProtectedRoute><Layout><PantryPage /></Layout></ProtectedRoute>} />
      <Route path="/suggestions" element={<ProtectedRoute><Layout><SuggestionsPage /></Layout></ProtectedRoute>} />
      <Route path="/chores" element={<ProtectedRoute><Layout><ChoresPage /></Layout></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><Layout><SettingsPage /></Layout></ProtectedRoute>} />
    </Routes>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
