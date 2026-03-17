import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI, familyAPI, settingsAPI } from '../lib/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [family, setFamily] = useState(null);
  const [familySettings, setFamilySettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
      setIsAuthenticated(true);
      loadUserData();
    }
    setLoading(false);
  }, []);

  const loadUserData = async () => {
    try {
      const [userRes, familyRes, settingsRes] = await Promise.all([
        authAPI.getMe(),
        familyAPI.get().catch(() => ({ data: null })),
        settingsAPI.get().catch(() => ({ data: null })),
      ]);
      if (userRes.data) {
        setUser(userRes.data);
        localStorage.setItem('user', JSON.stringify(userRes.data));
      }
      setFamily(familyRes.data);
      if (settingsRes.data) {
        setFamilySettings(settingsRes.data);
      }
    } catch (error) {
      console.error('Failed to load user data:', error);
    }
  };

  const loadFamily = async () => {
    try {
      const response = await familyAPI.get();
      setFamily(response.data);
    } catch (error) {
      console.error('Failed to load family:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const response = await settingsAPI.get();
      setFamilySettings(response.data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const login = async (email, password) => {
    const response = await authAPI.login({ email, password });
    const { token, user: userData } = response.data;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    setIsAuthenticated(true);
    await loadFamily();
    await loadSettings();
    return response.data;
  };

  const pinLogin = async (pin) => {
    const response = await authAPI.pinLogin(pin);
    const { token, family: familyData } = response.data;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify({ id: 'guest', name: 'Family Member', role: 'child' }));
    setUser({ id: 'guest', name: 'Family Member', role: 'child' });
    setFamily(familyData);
    setIsAuthenticated(true);
    await loadSettings();
    return response.data;
  };

  const userPinLogin = async (pin) => {
    const response = await authAPI.userPinLogin(pin);
    const { token, user: userData } = response.data;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    setIsAuthenticated(true);
    await loadFamily();
    await loadSettings();
    return response.data;
  };

  const register = async (name, email, password, familyName = null) => {
    const response = await authAPI.register({ name, email, password, family_name: familyName });
    const { token, user: userData } = response.data;
    if (token && userData) {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      setIsAuthenticated(true);
      await loadFamily();
      await loadSettings();
    }
    return response.data;
  };

  const createFamily = async (name) => {
    const response = await familyAPI.create({ name });
    setFamily(response.data);
    await loadUserData();
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setFamily(null);
    setFamilySettings(null);
    setIsAuthenticated(false);
  };

  const refreshUser = async () => {
    await loadUserData();
  };

  const isModuleVisible = (moduleKey) => {
    if (!user) return false;
    const role = user.role || 'member';
    if (role === 'owner') return true; // Owner always sees everything
    if (!familySettings?.modules?.[moduleKey]) return true; // Default: visible
    const mod = familySettings.modules[moduleKey];
    if (!mod.enabled) return false;
    return mod.visible_to?.includes(role) !== false;
  };

  const value = {
    user,
    family,
    familySettings,
    loading,
    isAuthenticated,
    login,
    pinLogin,
    userPinLogin,
    register,
    createFamily,
    logout,
    loadFamily,
    loadSettings,
    refreshUser,
    isModuleVisible,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
