import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../lib/api';
import { toast } from 'sonner';
import { Home, User, Lock, Mail, Users, KeyRound, ArrowRight, Sparkles, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const AuthPage = () => {
  const { login, pinLogin, userPinLogin, register } = useAuth();
  const [mode, setMode] = useState('pin'); // pin, login, register, forgot
  const [pinType, setPinType] = useState('family');
  const [loading, setLoading] = useState(false);
  
  const [pin, setPin] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [familyName, setFamilyName] = useState('');
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSent, setForgotSent] = useState(false);

  const handlePinLogin = async (e) => {
    e.preventDefault();
    if (pin.length < 4) {
      toast.error('PIN must be at least 4 digits');
      return;
    }
    setLoading(true);
    try {
      if (pinType === 'family') {
        await pinLogin(pin);
        toast.success('Welcome to your Family Hub!');
      } else {
        await userPinLogin(pin);
        toast.success('Welcome back!');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid PIN');
    }
    setLoading(false);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    }
    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!familyName.trim()) {
      toast.error('Please enter a family name');
      return;
    }
    setLoading(true);
    try {
      const result = await register(name, email, password, familyName);
      toast.success(`Family created! Your Family PIN is: ${result.family_pin}`, { duration: 10000 });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    }
    setLoading(false);
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!forgotEmail.trim()) {
      toast.error('Please enter your email');
      return;
    }
    setLoading(true);
    try {
      await authAPI.forgotPassword(forgotEmail);
      setForgotSent(true);
      toast.success('Check your email for a reset link');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send reset email');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-cream dark:bg-gray-900 flex">
      {/* Left side - Hero image */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1511895426328-dc8714191300?q=80&w=2070&auto=format&fit=crop"
          alt="Happy family"
          className="object-cover w-full h-full"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-terracotta/30 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-12 bg-gradient-to-t from-navy/80 to-transparent">
          <h2 className="text-4xl font-heading font-bold text-white mb-4">
            Your Family's Digital Home
          </h2>
          <p className="text-white/90 text-lg max-w-md">
            Keep everyone organized, connected, and happy with our all-in-one family hub.
          </p>
        </div>
      </div>

      {/* Right side - Auth forms */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-terracotta rounded-2xl mb-4 shadow-warm">
              <Home className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-heading font-bold text-navy dark:text-gray-100">Family Hub</h1>
            <p className="text-navy-light dark:text-gray-400 mt-2">Welcome home!</p>
          </div>

          {/* Auth Card */}
          <div className="card-cozy">
            {mode === 'forgot' ? (
              /* Forgot Password */
              <div className="space-y-6">
                <button
                  onClick={() => { setMode('login'); setForgotSent(false); setForgotEmail(''); }}
                  className="text-sm text-navy-light hover:text-navy flex items-center gap-1"
                  data-testid="back-to-login"
                >
                  <ArrowLeft className="w-4 h-4" /> Back to Sign In
                </button>
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-terracotta/10 rounded-xl mb-3">
                    <Mail className="w-6 h-6 text-terracotta" />
                  </div>
                  <h2 className="text-xl font-heading font-bold text-navy dark:text-gray-100">Forgot Password</h2>
                  <p className="text-sm text-navy-light dark:text-gray-400 mt-1">
                    We'll send you a link to reset your password
                  </p>
                </div>
                
                {forgotSent ? (
                  <div className="text-center space-y-4">
                    <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
                      <p className="text-green-700 dark:text-green-300 text-sm">
                        If an account exists for <strong>{forgotEmail}</strong>, a password reset link has been sent. Check your inbox (and spam folder).
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => { setForgotSent(false); setForgotEmail(''); }}
                      className="w-full"
                      data-testid="try-another-email"
                    >
                      Try another email
                    </Button>
                  </div>
                ) : (
                  <form onSubmit={handleForgotPassword} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">Email Address</label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-navy-light" />
                        <Input
                          type="email"
                          value={forgotEmail}
                          onChange={(e) => setForgotEmail(e.target.value)}
                          placeholder="you@example.com"
                          className="input-cozy pl-10"
                          data-testid="forgot-email-input"
                        />
                      </div>
                    </div>
                    <Button
                      type="submit"
                      disabled={loading || !forgotEmail.trim()}
                      className="btn-primary w-full"
                      data-testid="forgot-submit"
                    >
                      {loading ? 'Sending...' : 'Send Reset Link'}
                    </Button>
                  </form>
                )}
              </div>
            ) : (
              <Tabs value={mode} onValueChange={setMode} className="w-full">
                <TabsList className="grid w-full grid-cols-2 bg-cream dark:bg-gray-800 rounded-xl p-1 mb-6">
                  <TabsTrigger
                    value="pin"
                    className="rounded-lg data-[state=active]:bg-terracotta data-[state=active]:text-white"
                    data-testid="pin-tab"
                  >
                    <KeyRound className="w-4 h-4 mr-2" />
                    Family PIN
                  </TabsTrigger>
                  <TabsTrigger
                    value="login"
                    className="rounded-lg data-[state=active]:bg-terracotta data-[state=active]:text-white"
                    data-testid="login-tab"
                  >
                    <User className="w-4 h-4 mr-2" />
                    Account
                  </TabsTrigger>
                </TabsList>

                {/* PIN Login */}
                <TabsContent value="pin">
                  <form onSubmit={handlePinLogin} className="space-y-6">
                    <div className="flex gap-2 p-1 bg-cream dark:bg-gray-800 rounded-lg">
                      <button
                        type="button"
                        onClick={() => { setPinType('family'); setPin(''); }}
                        className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                          pinType === 'family' ? 'bg-sage text-white' : 'text-navy-light hover:bg-sunny/30'
                        }`}
                      >
                        <Users className="w-4 h-4 inline mr-1" /> Family PIN
                      </button>
                      <button
                        type="button"
                        onClick={() => { setPinType('personal'); setPin(''); }}
                        className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                          pinType === 'personal' ? 'bg-sage text-white' : 'text-navy-light hover:bg-sunny/30'
                        }`}
                      >
                        <User className="w-4 h-4 inline mr-1" /> My PIN
                      </button>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">
                        {pinType === 'family' ? 'Enter Family PIN (6 digits)' : 'Enter Your Personal PIN (4 digits)'}
                      </label>
                      <Input
                        type="password"
                        value={pin}
                        onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
                        placeholder={pinType === 'family' ? '••••••' : '••••'}
                        maxLength={pinType === 'family' ? 6 : 4}
                        className="input-cozy text-center text-2xl tracking-widest"
                        data-testid="pin-input"
                      />
                      <p className="text-sm text-navy-light mt-2 text-center font-handwritten">
                        {pinType === 'family' 
                          ? 'Ask a family member for the Family PIN!' 
                          : 'Use your personal PIN to access your account'}
                      </p>
                    </div>
                    <Button
                      type="submit"
                      disabled={loading || pin.length < 4}
                      className="btn-primary w-full"
                      data-testid="pin-submit"
                    >
                      {loading ? 'Entering...' : 'Enter Home'}
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </form>
                </TabsContent>

                {/* Account Login */}
                <TabsContent value="login">
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">Email</label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-navy-light" />
                        <Input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="you@example.com"
                          className="input-cozy pl-10"
                          data-testid="login-email"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">Password</label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-navy-light" />
                        <Input
                          type="password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="••••••••"
                          className="input-cozy pl-10"
                          data-testid="login-password"
                        />
                      </div>
                    </div>
                    <div className="text-right">
                      <button
                        type="button"
                        onClick={() => { setMode('forgot'); setForgotSent(false); setForgotEmail(email); }}
                        className="text-sm text-terracotta hover:underline"
                        data-testid="forgot-password-link"
                      >
                        Forgot Password?
                      </button>
                    </div>
                    <Button
                      type="submit"
                      disabled={loading}
                      className="btn-primary w-full"
                      data-testid="login-submit"
                    >
                      {loading ? 'Logging in...' : 'Sign In'}
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </form>

                  <div className="mt-6 pt-6 border-t border-sunny/30">
                    <p className="text-center text-navy-light text-sm">
                      New here?{' '}
                      <button
                        onClick={() => setMode('register')}
                        className="text-terracotta font-medium hover:underline"
                        data-testid="goto-register"
                      >
                        Create an account
                      </button>
                    </p>
                  </div>
                </TabsContent>

                {/* Register */}
                <TabsContent value="register">
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="bg-sage/10 rounded-xl p-4 mb-2">
                      <p className="text-sage text-sm flex items-center gap-2">
                        <Home className="w-4 h-4" />
                        Create your account and family hub in one step!
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">Your Name</label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-navy-light" />
                        <Input
                          type="text"
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          placeholder="John Doe"
                          className="input-cozy pl-10"
                          data-testid="register-name"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">Family Name</label>
                      <div className="relative">
                        <Home className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-navy-light" />
                        <Input
                          type="text"
                          value={familyName}
                          onChange={(e) => setFamilyName(e.target.value)}
                          placeholder="The Smiths"
                          className="input-cozy pl-10"
                          data-testid="register-family-name"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">Email</label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-navy-light" />
                        <Input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="you@example.com"
                          className="input-cozy pl-10"
                          data-testid="register-email"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">Password</label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-navy-light" />
                        <Input
                          type="password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="••••••••"
                          className="input-cozy pl-10"
                          data-testid="register-password"
                        />
                      </div>
                    </div>
                    <Button
                      type="submit"
                      disabled={loading || !name || !email || !password || !familyName}
                      className="btn-primary w-full"
                      data-testid="register-submit"
                    >
                      {loading ? 'Creating...' : 'Create Family Hub'}
                      <Sparkles className="w-4 h-4 ml-2" />
                    </Button>
                    <p className="text-xs text-navy-light text-center">
                      A 6-digit Family PIN will be auto-generated for easy member access
                    </p>
                  </form>

                  <div className="mt-6 pt-6 border-t border-sunny/30">
                    <p className="text-center text-navy-light text-sm">
                      Already have an account?{' '}
                      <button
                        onClick={() => setMode('login')}
                        className="text-terracotta font-medium hover:underline"
                        data-testid="goto-login"
                      >
                        Sign in
                      </button>
                    </p>
                  </div>
                </TabsContent>

              </Tabs>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
