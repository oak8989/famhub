import axios from 'axios';

const getApiUrl = () => {
  const envUrl = process.env.REACT_APP_BACKEND_URL;
  if (envUrl) {
    return envUrl + '/api';
  }
  return '/api';
};

const api = axios.create({
  baseURL: getApiUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  pinLogin: (pin) => api.post('/auth/pin-login', { pin }),
  userPinLogin: (pin) => api.post('/auth/user-pin-login', { pin }),
  getMe: () => api.get('/auth/me'),
  changePassword: (data) => api.post('/auth/change-password', data),
  resetPassword: (userId) => api.post('/auth/reset-password', { user_id: userId }),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPasswordToken: (token, newPassword) => api.post('/auth/reset-password-token', { token, new_password: newPassword }),
  updateHiddenModules: (hiddenModules) => api.put('/auth/hidden-modules', { hidden_modules: hiddenModules }),
};

// Family
export const familyAPI = {
  create: (data) => api.post('/family/create', data),
  get: () => api.get('/family'),
  update: (data) => api.put('/family', data),
  getMembers: () => api.get('/family/members'),
  join: (familyId) => api.post(`/family/join/${familyId}`),
  invite: (data) => api.post('/family/invite', data),
  updateMemberRole: (memberId, role) => api.put(`/family/members/${memberId}/role`, { role }),
  removeMember: (memberId) => api.delete(`/family/members/${memberId}`),
  regenerateFamilyPin: () => api.post('/family/regenerate-pin'),
  regenerateUserPin: (memberId) => api.post(`/family/members/${memberId}/regenerate-pin`),
};

// Settings
export const settingsAPI = {
  get: () => api.get('/settings'),
  update: (data) => api.put('/settings', data),
  getServer: () => api.get('/settings/server'),
};

// Calendar
export const calendarAPI = {
  getEvents: () => api.get('/calendar'),
  createEvent: (data) => api.post('/calendar', data),
  updateEvent: (id, data) => api.put(`/calendar/${id}`, data),
  deleteEvent: (id) => api.delete(`/calendar/${id}`),
  googleAuth: () => api.get('/calendar/google/auth'),
  googleSync: () => api.post('/calendar/google/sync'),
  googleDisconnect: () => api.delete('/calendar/google/disconnect'),
};

// Shopping List
export const shoppingAPI = {
  getItems: () => api.get('/shopping'),
  createItem: (data) => api.post('/shopping', data),
  updateItem: (id, data) => api.put(`/shopping/${id}`, data),
  deleteItem: (id) => api.delete(`/shopping/${id}`),
  clearChecked: () => api.delete('/shopping'),
};

// Tasks
export const tasksAPI = {
  getTasks: () => api.get('/tasks'),
  createTask: (data) => api.post('/tasks', data),
  updateTask: (id, data) => api.put(`/tasks/${id}`, data),
  deleteTask: (id) => api.delete(`/tasks/${id}`),
};

// Chores & Rewards
export const choresAPI = {
  getChores: () => api.get('/chores'),
  createChore: (data) => api.post('/chores', data),
  updateChore: (id, data) => api.put(`/chores/${id}`, data),
  completeChore: (id) => api.post(`/chores/${id}/complete`),
  deleteChore: (id) => api.delete(`/chores/${id}`),
  getRewards: () => api.get('/rewards'),
  createReward: (data) => api.post('/rewards', data),
  claimReward: (data) => api.post('/rewards/claim', data),
  deleteReward: (id) => api.delete(`/rewards/${id}`),
  getLeaderboard: () => api.get('/leaderboard'),
  getRewardClaims: () => api.get('/reward-claims'),
};

// Notes
export const notesAPI = {
  getNotes: () => api.get('/notes'),
  createNote: (data) => api.post('/notes', data),
  updateNote: (id, data) => api.put(`/notes/${id}`, data),
  deleteNote: (id) => api.delete(`/notes/${id}`),
};

// Budget
export const budgetAPI = {
  getEntries: () => api.get('/budget'),
  createEntry: (data) => api.post('/budget', data),
  updateEntry: (id, data) => api.put(`/budget/${id}`, data),
  deleteEntry: (id) => api.delete(`/budget/${id}`),
  getSummary: () => api.get('/budget/summary'),
};

// Meal Plans
export const mealPlanAPI = {
  getPlans: () => api.get('/meals'),
  createPlan: (data) => api.post('/meals', data),
  updatePlan: (id, data) => api.put(`/meals/${id}`, data),
  deletePlan: (id) => api.delete(`/meals/${id}`),
};

// Recipes
export const recipesAPI = {
  getRecipes: () => api.get('/recipes'),
  getRecipe: (id) => api.get(`/recipes/${id}`),
  createRecipe: (data) => api.post('/recipes', data),
  updateRecipe: (id, data) => api.put(`/recipes/${id}`, data),
  deleteRecipe: (id) => api.delete(`/recipes/${id}`),
  importFromURL: (url) => api.post('/recipes/import-url', { url }),
};

// Grocery List
export const groceryAPI = {
  getItems: () => api.get('/grocery'),
  createItem: (data) => api.post('/grocery', data),
  updateItem: (id, data) => api.put(`/grocery/${id}`, data),
  deleteItem: (id) => api.delete(`/grocery/${id}`),
  clearChecked: () => api.delete('/grocery'),
  addFromMeal: (planId) => api.post(`/grocery/add-from-meal/${planId}`),
};

// Contacts
export const contactsAPI = {
  getContacts: () => api.get('/contacts'),
  createContact: (data) => api.post('/contacts', data),
  updateContact: (id, data) => api.put(`/contacts/${id}`, data),
  deleteContact: (id) => api.delete(`/contacts/${id}`),
};

// Pantry
export const pantryAPI = {
  getItems: () => api.get('/pantry'),
  createItem: (data) => api.post('/pantry', data),
  updateItem: (id, data) => api.put(`/pantry/${id}`, data),
  deleteItem: (id) => api.delete(`/pantry/${id}`),
  lookupBarcode: (barcode) => api.get(`/pantry/barcode/${barcode}`),
  bulkAdd: (items) => api.post('/pantry/bulk-add', items),
};

// Meal Suggestions
export const suggestionsAPI = {
  getSuggestions: () => api.get('/suggestions'),
  getAISuggestions: () => api.post('/suggestions/ai', { use_ai: true }),
};

// QR Code
export const qrCodeAPI = {
  getQRCode: (url) => api.get(`/qr-code/base64?url=${encodeURIComponent(url)}`),
};

// Push Notifications
export const notificationsAPI = {
  getVapidKey: () => api.get('/notifications/vapid-key'),
  subscribe: (subscription) => api.post('/notifications/subscribe', subscription),
  unsubscribe: () => api.delete('/notifications/unsubscribe'),
};

// Admin (Owner only)
export const adminAPI = {
  getStatus: () => api.get('/admin/status'),
  getConfig: () => api.get('/admin/config'),
  saveSmtp: (data) => api.post('/admin/config/smtp', data),
  saveGoogle: (data) => api.post('/admin/config/google', data),
  saveOpenai: (data) => api.post('/admin/config/openai', data),
  saveServer: (data) => api.post('/admin/config/server', data),
  testEmail: () => api.post('/admin/test-email'),
  getLogs: (type = 'backend') => api.get(`/admin/logs?type=${type}`),
  reboot: () => api.post('/admin/reboot'),
};

// Data Export & Import
export const exportAPI = {
  exportAllData: () => api.get('/export/data', { responseType: 'blob' }),
  exportModuleCSV: (module) => api.get(`/export/csv/${module}`, { responseType: 'blob' }),
};

export const importAPI = {
  importData: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/import/data', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// NOK Box (In Case of Emergency)
export const nokBoxAPI = {
  getEntries: () => api.get('/nok-box'),
  createEntry: (data) => api.post('/nok-box', data),
  updateEntry: (id, data) => api.put(`/nok-box/${id}`, data),
  deleteEntry: (id) => api.delete(`/nok-box/${id}`),
  uploadFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/nok-box/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Household Inventory
export const inventoryAPI = {
  getItems: () => api.get('/inventory'),
  createItem: (data) => api.post('/inventory', data),
  updateItem: (id, data) => api.put(`/inventory/${id}`, data),
  deleteItem: (id) => api.delete(`/inventory/${id}`),
  bulkAdd: (items) => api.post('/inventory/bulk-add', items),
  lookupBarcode: (barcode) => api.get(`/inventory/barcode/${barcode}`),
};

export default api;
