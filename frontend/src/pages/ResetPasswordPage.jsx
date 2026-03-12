import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { authAPI } from '../lib/api';
import { toast } from 'sonner';
import { Home, Lock, Check, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleReset = async (e) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    if (!token) {
      toast.error('Invalid reset link');
      return;
    }
    setLoading(true);
    try {
      const res = await authAPI.resetPasswordToken(token, newPassword);
      toast.success(res.data.message);
      setSuccess(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-cream dark:bg-gray-900 flex items-center justify-center p-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-terracotta rounded-2xl mb-4 shadow-warm">
            <Home className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-heading font-bold text-navy dark:text-gray-100">Family Hub</h1>
          <p className="text-navy-light dark:text-gray-400 mt-2">Reset your password</p>
        </div>

        <div className="card-cozy">
          {success ? (
            <div className="text-center space-y-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full">
                <Check className="w-8 h-8 text-green-600" />
              </div>
              <div>
                <h2 className="text-xl font-heading font-bold text-navy dark:text-gray-100 mb-2">Password Reset!</h2>
                <p className="text-navy-light dark:text-gray-400 text-sm">Your password has been updated. You can now sign in.</p>
              </div>
              <Button
                onClick={() => navigate('/')}
                className="btn-primary w-full"
                data-testid="go-to-login-btn"
              >
                Go to Sign In
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          ) : !token ? (
            <div className="text-center space-y-4">
              <p className="text-red-600 dark:text-red-400">Invalid or missing reset token. Please request a new reset link from the login page.</p>
              <Button
                onClick={() => navigate('/')}
                variant="outline"
                className="w-full"
                data-testid="go-to-login-btn"
              >
                Go to Login
              </Button>
            </div>
          ) : (
            <form onSubmit={handleReset} className="space-y-4">
              <div className="text-center mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-terracotta/10 rounded-xl mb-3">
                  <Lock className="w-6 h-6 text-terracotta" />
                </div>
                <h2 className="text-xl font-heading font-bold text-navy dark:text-gray-100">Choose New Password</h2>
                <p className="text-sm text-navy-light dark:text-gray-400 mt-1">Enter your new password below</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">New Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-navy-light" />
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="At least 6 characters"
                    className="input-cozy pl-10"
                    data-testid="new-password-input"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-navy dark:text-gray-300 mb-2">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-navy-light" />
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter password"
                    className="input-cozy pl-10"
                    data-testid="confirm-password-input"
                  />
                </div>
              </div>
              <Button
                type="submit"
                disabled={loading || !newPassword || !confirmPassword}
                className="btn-primary w-full"
                data-testid="reset-submit"
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
