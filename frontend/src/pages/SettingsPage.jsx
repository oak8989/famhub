import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { 
  Settings, Users, Shield, Calendar, UserPlus, Trash2, 
  RefreshCw, Server, Check, X, Crown, Eye, EyeOff, Copy, Key,
  QrCode, Download, Bell, BellOff, Smartphone, Upload, Loader2
} from 'lucide-react';
import api, { qrCodeAPI, notificationsAPI, exportAPI, importAPI } from '../lib/api';

const ROLE_COLORS = {
  owner: 'bg-amber-500',
  parent: 'bg-blue-500',
  member: 'bg-green-500',
  child: 'bg-purple-500',
};

const ROLE_LABELS = {
  owner: 'Owner',
  parent: 'Parent',
  member: 'Family Member',
  child: 'Child',
};

const MODULE_NAMES = {
  calendar: 'Calendar',
  shopping: 'Shopping List',
  tasks: 'Tasks',
  notes: 'Notes',
  budget: 'Budget',
  meals: 'Meal Planner',
  recipes: 'Recipe Box',
  grocery: 'Grocery List',
  contacts: 'Contacts',
  pantry: 'Pantry',
  suggestions: 'Meal Ideas',
  chores: 'Chores & Rewards',
};

const SettingsPage = () => {
  const { user, family, loadFamily, refreshUser } = useAuth();
  const [searchParams] = useSearchParams();
  const [members, setMembers] = useState([]);
  const [settings, setSettings] = useState(null);
  const [familyName, setFamilyName] = useState('');
  const [familyPin, setFamilyPin] = useState('');
  const [showPin, setShowPin] = useState(false);
  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [newMember, setNewMember] = useState({ name: '', email: '', role: 'member' });
  const [newMemberResult, setNewMemberResult] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // New state for QR, notifications, exports
  const [qrCode, setQrCode] = useState(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);

  const isAdmin = user?.role === 'owner' || user?.role === 'parent';
  const isOwner = user?.role === 'owner';

  useEffect(() => {
    loadData();
    
    if (searchParams.get('google_connected') === 'true') {
      toast.success('Google Calendar connected successfully!');
    }
    if (searchParams.get('error') === 'google_auth_failed') {
      toast.error('Failed to connect Google Calendar');
    }
  }, [searchParams]);

  const loadData = async () => {
    try {
      const [membersRes, settingsRes, familyRes] = await Promise.all([
        api.get('/family/members'),
        api.get('/settings'),
        api.get('/family'),
      ]);
      setMembers(membersRes.data || []);
      setSettings(settingsRes.data);
      if (familyRes.data) {
        setFamilyName(familyRes.data.name || '');
        setFamilyPin(familyRes.data.pin || '');
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateFamilyName = async () => {
    try {
      await api.put('/family', { name: familyName });
      toast.success('Family name updated');
      loadFamily();
    } catch (error) {
      toast.error('Failed to update family name');
    }
  };

  const handleRegenerateFamilyPin = async () => {
    try {
      const res = await api.post('/family/regenerate-pin');
      setFamilyPin(res.data.pin);
      toast.success(`New Family PIN: ${res.data.pin}`);
    } catch (error) {
      toast.error('Failed to regenerate PIN');
    }
  };

  const handleAddMember = async () => {
    if (!newMember.name.trim()) {
      toast.error('Please enter a name');
      return;
    }
    try {
      const res = await api.post('/family/add-member', newMember);
      setNewMemberResult(res.data);
      toast.success(`${newMember.name} added to family!`);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add member');
    }
  };

  const handleCloseAddMember = () => {
    setAddMemberOpen(false);
    setNewMember({ name: '', email: '', role: 'member' });
    setNewMemberResult(null);
  };

  const handleUpdateRole = async (memberId, newRole) => {
    try {
      await api.put(`/family/members/${memberId}/role`, { role: newRole });
      toast.success('Role updated');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;
    try {
      await api.delete(`/family/members/${memberId}`);
      toast.success('Member removed');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to remove member');
    }
  };

  const handleRegenerateUserPin = async (memberId, memberName) => {
    try {
      const res = await api.post(`/family/members/${memberId}/regenerate-pin`);
      toast.success(`New PIN for ${memberName}: ${res.data.pin}`, { duration: 10000 });
    } catch (error) {
      toast.error('Failed to regenerate PIN');
    }
  };

  const handleModuleToggle = async (module, enabled) => {
    const newSettings = { ...settings };
    newSettings.modules[module].enabled = enabled;
    setSettings(newSettings);
    try {
      await api.put('/settings', { modules: newSettings.modules });
      toast.success('Settings saved');
    } catch (error) {
      toast.error('Failed to save settings');
    }
  };

  const handleModuleVisibility = async (module, role, visible) => {
    const newSettings = { ...settings };
    const visibleTo = newSettings.modules[module].visible_to || [];
    
    if (visible && !visibleTo.includes(role)) {
      visibleTo.push(role);
    } else if (!visible) {
      const index = visibleTo.indexOf(role);
      if (index > -1) visibleTo.splice(index, 1);
    }
    
    newSettings.modules[module].visible_to = visibleTo;
    setSettings(newSettings);
    
    try {
      await api.put('/settings', { modules: newSettings.modules });
    } catch (error) {
      toast.error('Failed to save settings');
    }
  };

  const handleConnectGoogle = async () => {
    try {
      const res = await api.get('/calendar/google/auth');
      window.location.href = res.data.authorization_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Google Calendar not configured');
    }
  };

  const handleDisconnectGoogle = async () => {
    try {
      await api.delete('/calendar/google/disconnect');
      toast.success('Google Calendar disconnected');
      refreshUser();
    } catch (error) {
      toast.error('Failed to disconnect');
    }
  };

  const handleSyncGoogle = async () => {
    try {
      const res = await api.post('/calendar/google/sync');
      toast.success(`Synced ${res.data.synced} events to Google Calendar`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sync');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="settings-page">
      <div className="flex items-center gap-3">
        <Settings className="w-8 h-8 text-terracotta" />
        <div>
          <h1 className="text-2xl font-heading font-bold text-navy">Settings</h1>
          <p className="text-navy-light">Manage your family hub</p>
        </div>
      </div>

      <Tabs defaultValue="family" className="space-y-4">
        <TabsList className="bg-warm-white flex-wrap">
          <TabsTrigger value="family" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
            <Users className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Family</span>
          </TabsTrigger>
          {isAdmin && (
            <>
              <TabsTrigger value="modules" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
                <Shield className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Modules</span>
              </TabsTrigger>
              <TabsTrigger value="integrations" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
                <Calendar className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Integrations</span>
              </TabsTrigger>
            </>
          )}
          <TabsTrigger value="mobile" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
            <Smartphone className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Mobile</span>
          </TabsTrigger>
          <TabsTrigger value="backup" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
            <Download className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Backup</span>
          </TabsTrigger>
          {isOwner && (
            <TabsTrigger value="server" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
              <Server className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Server</span>
            </TabsTrigger>
          )}
        </TabsList>

        {/* Family Tab */}
        <TabsContent value="family" className="space-y-4">
          {/* Family Info Card */}
          <Card className="card-base">
            <CardHeader>
              <CardTitle className="text-navy">Family Information</CardTitle>
              <CardDescription>Your family PIN allows quick access for all members</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Family Name</Label>
                  <div className="flex gap-2">
                    <Input
                      value={familyName}
                      onChange={(e) => setFamilyName(e.target.value)}
                      disabled={!isAdmin}
                      data-testid="family-name-input"
                    />
                    {isAdmin && (
                      <Button onClick={handleUpdateFamilyName} data-testid="save-family-name-btn">
                        Save
                      </Button>
                    )}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Key className="w-4 h-4" /> Family PIN (Auto-Generated)
                  </Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Input
                        type={showPin ? 'text' : 'password'}
                        value={familyPin}
                        readOnly
                        className="font-mono text-lg tracking-widest"
                        data-testid="family-pin-input"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPin(!showPin)}
                        className="absolute right-10 top-1/2 -translate-y-1/2 text-navy-light hover:text-navy"
                      >
                        {showPin ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(familyPin)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-navy-light hover:text-navy"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    {isAdmin && (
                      <Button variant="outline" onClick={handleRegenerateFamilyPin} title="Generate New PIN" data-testid="regenerate-pin-btn">
                        <RefreshCw className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-navy-light">Share this PIN with family members for quick login</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Members Card */}
          <Card className="card-base">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-navy">Family Members</CardTitle>
                <CardDescription>Add and manage family members</CardDescription>
              </div>
              {isAdmin && (
                <Dialog open={addMemberOpen} onOpenChange={(open) => { if (!open) handleCloseAddMember(); else setAddMemberOpen(true); }}>
                  <DialogTrigger asChild>
                    <Button className="bg-sage hover:bg-sage/90" data-testid="add-member-btn">
                      <UserPlus className="w-4 h-4 mr-2" /> Add Member
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Family Member</DialogTitle>
                    </DialogHeader>
                    {newMemberResult ? (
                      <div className="space-y-4 pt-4">
                        <div className="text-center p-4 bg-green-50 rounded-xl">
                          <Check className="w-12 h-12 text-green-500 mx-auto mb-2" />
                          <h3 className="font-bold text-navy text-lg">{newMemberResult.name} Added!</h3>
                          {newMemberResult.email_sent ? (
                            <p className="text-green-600">Invitation email sent!</p>
                          ) : newMemberResult.email_error ? (
                            <p className="text-amber-600 text-sm">{newMemberResult.email_error}</p>
                          ) : (
                            <p className="text-navy-light">Share their PIN so they can login</p>
                          )}
                        </div>
                        <div className="p-4 bg-cream rounded-xl">
                          <Label className="text-sm text-navy-light">Login PIN</Label>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-3xl font-mono font-bold text-navy tracking-widest">{newMemberResult.user_pin}</span>
                            <Button variant="ghost" size="icon" onClick={() => copyToClipboard(newMemberResult.user_pin)}>
                              <Copy className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                        {newMemberResult.temp_password && (
                          <div className="p-4 bg-cream rounded-xl">
                            <Label className="text-sm text-navy-light">Temporary Password</Label>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="font-mono font-bold text-navy">{newMemberResult.temp_password}</span>
                              <Button variant="ghost" size="icon" onClick={() => copyToClipboard(newMemberResult.temp_password)}>
                                <Copy className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        )}
                        <p className="text-sm text-navy-light text-center">
                          {newMemberResult.name} can use this PIN on the login screen to access Family Hub
                        </p>
                        <Button onClick={handleCloseAddMember} className="w-full">Done</Button>
                      </div>
                    ) : (
                      <div className="space-y-4 pt-4">
                        <div className="space-y-2">
                          <Label>Name</Label>
                          <Input
                            value={newMember.name}
                            onChange={(e) => setNewMember({ ...newMember, name: e.target.value })}
                            placeholder="Enter name"
                            data-testid="new-member-name-input"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Email (Optional - for invite)</Label>
                          <Input
                            type="email"
                            value={newMember.email}
                            onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
                            placeholder="email@example.com"
                            data-testid="new-member-email-input"
                          />
                          <p className="text-xs text-navy-light">
                            If provided, an invitation email will be sent (requires SMTP setup)
                          </p>
                        </div>
                        <div className="space-y-2">
                          <Label>Role</Label>
                          <Select
                            value={newMember.role}
                            onValueChange={(value) => setNewMember({ ...newMember, role: value })}
                          >
                            <SelectTrigger data-testid="new-member-role-select">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="parent">Parent (Can manage family)</SelectItem>
                              <SelectItem value="member">Family Member</SelectItem>
                              <SelectItem value="child">Child (Limited access)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <Button onClick={handleAddMember} className="w-full bg-sage hover:bg-sage/90" data-testid="confirm-add-member-btn">
                          <UserPlus className="w-4 h-4 mr-2" /> Add to Family
                        </Button>
                        <p className="text-xs text-navy-light text-center">
                          A unique PIN will be auto-generated for this member
                        </p>
                      </div>
                    )}
                  </DialogContent>
                </Dialog>
              )}
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {members.length === 0 ? (
                  <p className="text-center py-8 text-navy-light">No family members yet. Add someone!</p>
                ) : (
                  members.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-3 bg-cream rounded-xl"
                      data-testid={`member-${member.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <Avatar className="w-10 h-10">
                          <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${member.avatar_seed}`} />
                          <AvatarFallback>{member.name?.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-navy">{member.name}</span>
                            {member.role === 'owner' && <Crown className="w-4 h-4 text-amber-500" />}
                          </div>
                          <div className="flex items-center gap-2">
                            {member.email && <span className="text-sm text-navy-light">{member.email}</span>}
                            {member.user_pin && (
                              <span className="text-xs text-navy-light font-mono">PIN: {member.user_pin}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={`${ROLE_COLORS[member.role]} text-white`}>
                          {ROLE_LABELS[member.role]}
                        </Badge>
                        {member.points > 0 && (
                          <Badge variant="outline">{member.points} pts</Badge>
                        )}
                        {isAdmin && member.id !== user?.id && member.role !== 'owner' && (
                          <Select
                            value={member.role}
                            onValueChange={(value) => handleUpdateRole(member.id, value)}
                          >
                            <SelectTrigger className="w-28 h-8 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="parent">Parent</SelectItem>
                              <SelectItem value="member">Member</SelectItem>
                              <SelectItem value="child">Child</SelectItem>
                            </SelectContent>
                          </Select>
                        )}
                        {isAdmin && member.id !== user?.id && (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleRegenerateUserPin(member.id, member.name)}
                              title="Generate New PIN"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </Button>
                            {member.role !== 'owner' && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleRemoveMember(member.id)}
                                className="text-red-500 hover:text-red-600 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Modules Tab */}
        {isAdmin && (
          <TabsContent value="modules" className="space-y-4">
            <Card className="card-base">
              <CardHeader>
                <CardTitle className="text-navy">Module Settings</CardTitle>
                <CardDescription>Control which features are available and who can see them</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {settings?.modules && Object.entries(settings.modules).map(([key, module]) => (
                    <div key={key} className="p-4 bg-cream rounded-xl space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-navy">{MODULE_NAMES[key] || key}</span>
                        <Switch
                          checked={module.enabled}
                          onCheckedChange={(checked) => handleModuleToggle(key, checked)}
                          data-testid={`module-toggle-${key}`}
                        />
                      </div>
                      {module.enabled && (
                        <div className="flex flex-wrap gap-2 pt-2 border-t border-sunny/30">
                          <span className="text-sm text-navy-light mr-2">Visible to:</span>
                          {['owner', 'parent', 'member', 'child'].map((role) => (
                            <button
                              key={role}
                              onClick={() => handleModuleVisibility(key, role, !module.visible_to?.includes(role))}
                              className={`px-2 py-1 text-xs rounded-full transition-colors ${
                                module.visible_to?.includes(role)
                                  ? `${ROLE_COLORS[role]} text-white`
                                  : 'bg-gray-200 text-gray-500'
                              }`}
                            >
                              {ROLE_LABELS[role]}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Integrations Tab */}
        {isAdmin && (
          <TabsContent value="integrations" className="space-y-4">
            <Card className="card-base">
              <CardHeader>
                <CardTitle className="text-navy flex items-center gap-2">
                  <Calendar className="w-5 h-5" /> Google Calendar
                </CardTitle>
                <CardDescription>Sync your family calendar with Google Calendar</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {user?.google_tokens ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-5 h-5" />
                      <span>Connected to Google Calendar</span>
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={handleSyncGoogle} data-testid="sync-google-btn">
                        <RefreshCw className="w-4 h-4 mr-2" /> Sync Now
                      </Button>
                      <Button variant="outline" onClick={handleDisconnectGoogle} data-testid="disconnect-google-btn">
                        <X className="w-4 h-4 mr-2" /> Disconnect
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Button onClick={handleConnectGoogle} data-testid="connect-google-btn">
                      <Calendar className="w-4 h-4 mr-2" /> Connect Google Calendar
                    </Button>
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <p className="text-sm text-amber-700">
                        <strong>Note:</strong> Google Calendar requires setup. Add these environment variables to your server:
                      </p>
                      <ul className="text-xs text-amber-600 mt-2 space-y-1 list-disc list-inside">
                        <li>GOOGLE_CLIENT_ID</li>
                        <li>GOOGLE_CLIENT_SECRET</li>
                        <li>GOOGLE_REDIRECT_URI</li>
                      </ul>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Server Tab */}
        {isOwner && (
          <TabsContent value="server" className="space-y-4">
            <Card className="card-base">
              <CardHeader>
                <CardTitle className="text-navy">Server Configuration</CardTitle>
                <CardDescription>These settings are configured in your server's environment variables</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-cream rounded-xl">
                  <h3 className="font-medium text-navy mb-2">SMTP Email Settings (Optional)</h3>
                  <p className="text-sm text-navy-light mb-4">
                    Configure these to enable email invitations:
                  </p>
                  <pre className="bg-navy text-cream p-3 rounded-lg text-sm overflow-x-auto">
{`SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=Family Hub <noreply@familyhub.local>`}
                  </pre>
                </div>
                <div className="p-4 bg-cream rounded-xl">
                  <h3 className="font-medium text-navy mb-2">Google Calendar (Optional)</h3>
                  <p className="text-sm text-navy-light mb-4">
                    To enable Google Calendar sync:
                  </p>
                  <pre className="bg-navy text-cream p-3 rounded-lg text-sm overflow-x-auto">
{`GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/api/calendar/google/callback`}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Mobile Setup Tab */}
        <TabsContent value="mobile" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <QrCode className="w-5 h-5 text-terracotta" />
                Mobile Setup
              </CardTitle>
              <CardDescription>Easily connect mobile devices to your Family Hub</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* QR Code Section */}
              <div className="p-4 bg-cream rounded-xl">
                <h3 className="font-medium text-navy mb-2">Quick Connect with QR Code</h3>
                <p className="text-sm text-navy-light mb-4">
                  Scan this QR code with your phone to quickly set up the server URL
                </p>
                <div className="flex flex-col items-center gap-4">
                  {qrCode ? (
                    <img 
                      src={qrCode} 
                      alt="Server URL QR Code" 
                      className="w-48 h-48 border rounded-xl"
                      data-testid="qr-code-image"
                    />
                  ) : (
                    <div className="w-48 h-48 border-2 border-dashed border-gray-300 rounded-xl flex items-center justify-center">
                      <QrCode className="w-12 h-12 text-gray-300" />
                    </div>
                  )}
                  <Button
                    onClick={async () => {
                      try {
                        const serverUrl = window.location.origin;
                        const response = await qrCodeAPI.getQRCode(serverUrl);
                        setQrCode(response.data.qr_code);
                        toast.success('QR code generated!');
                      } catch (error) {
                        toast.error('Failed to generate QR code');
                      }
                    }}
                    className="btn-secondary"
                    data-testid="generate-qr-btn"
                  >
                    <QrCode className="w-4 h-4 mr-2" />
                    Generate QR Code
                  </Button>
                </div>
              </div>

              {/* Push Notifications Section */}
              <div className="p-4 bg-cream rounded-xl">
                <h3 className="font-medium text-navy mb-2 flex items-center gap-2">
                  <Bell className="w-5 h-5" />
                  Push Notifications
                </h3>
                <p className="text-sm text-navy-light mb-4">
                  Get notified about tasks, events, and chores
                </p>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-navy">
                      {notificationsEnabled ? 'Notifications enabled' : 'Notifications disabled'}
                    </p>
                    <p className="text-xs text-navy-light">
                      {notificationsEnabled ? 'You will receive browser notifications' : 'Enable to stay updated'}
                    </p>
                  </div>
                  <Button
                    variant={notificationsEnabled ? 'outline' : 'default'}
                    onClick={async () => {
                      if (notificationsEnabled) {
                        try {
                          await notificationsAPI.unsubscribe();
                          setNotificationsEnabled(false);
                          toast.success('Notifications disabled');
                        } catch (error) {
                          toast.error('Failed to disable notifications');
                        }
                      } else {
                        try {
                          const permission = await Notification.requestPermission();
                          if (permission === 'granted') {
                            // For now, just mark as enabled - full implementation would use service workers
                            setNotificationsEnabled(true);
                            toast.success('Notifications enabled!');
                          } else {
                            toast.error('Notification permission denied');
                          }
                        } catch (error) {
                          toast.error('Notifications not supported');
                        }
                      }
                    }}
                    className={notificationsEnabled ? 'border-red-300 text-red-600' : 'btn-primary'}
                    data-testid="toggle-notifications-btn"
                  >
                    {notificationsEnabled ? (
                      <>
                        <BellOff className="w-4 h-4 mr-2" />
                        Disable
                      </>
                    ) : (
                      <>
                        <Bell className="w-4 h-4 mr-2" />
                        Enable
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Data Backup Tab */}
        <TabsContent value="backup" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="w-5 h-5 text-terracotta" />
                Data Export & Backup
              </CardTitle>
              <CardDescription>Download your family data for backup or migration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Full Backup */}
              <div className="p-4 bg-cream rounded-xl">
                <h3 className="font-medium text-navy mb-2">Full Data Backup</h3>
                <p className="text-sm text-navy-light mb-4">
                  Download all your family data as a JSON file. Includes members, events, tasks, recipes, and more.
                </p>
                <Button
                  onClick={async () => {
                    setExportLoading(true);
                    try {
                      const response = await exportAPI.exportAllData();
                      const url = window.URL.createObjectURL(new Blob([response.data]));
                      const link = document.createElement('a');
                      link.href = url;
                      link.setAttribute('download', `family-hub-backup-${new Date().toISOString().split('T')[0]}.json`);
                      document.body.appendChild(link);
                      link.click();
                      link.remove();
                      toast.success('Backup downloaded!');
                    } catch (error) {
                      toast.error('Failed to export data');
                    }
                    setExportLoading(false);
                  }}
                  disabled={exportLoading}
                  className="btn-primary w-full sm:w-auto"
                  data-testid="export-all-btn"
                >
                  {exportLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 mr-2" />
                      Download Full Backup (JSON)
                    </>
                  )}
                </Button>
              </div>

              {/* Module-specific exports */}
              <div className="p-4 bg-cream rounded-xl">
                <h3 className="font-medium text-navy mb-2">Export by Module (CSV)</h3>
                <p className="text-sm text-navy-light mb-4">
                  Download specific modules as spreadsheet-compatible CSV files.
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {['calendar', 'shopping', 'tasks', 'chores', 'budget', 'contacts', 'pantry'].map((module) => (
                    <Button
                      key={module}
                      variant="outline"
                      size="sm"
                      onClick={async () => {
                        try {
                          const response = await exportAPI.exportModuleCSV(module);
                          const url = window.URL.createObjectURL(new Blob([response.data]));
                          const link = document.createElement('a');
                          link.href = url;
                          link.setAttribute('download', `${module}-export-${new Date().toISOString().split('T')[0]}.csv`);
                          document.body.appendChild(link);
                          link.click();
                          link.remove();
                          toast.success(`${module} exported!`);
                        } catch (error) {
                          toast.error(`Failed to export ${module}`);
                        }
                      }}
                      className="capitalize"
                      data-testid={`export-${module}-btn`}
                    >
                      <Download className="w-3 h-3 mr-1" />
                      {module}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Info */}
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  <strong>Tip:</strong> Regular backups help protect your family data. We recommend downloading a backup at least once a month.
                </p>
              </div>

              {/* Data Import */}
              <div className="p-4 bg-cream dark:bg-gray-700/30 rounded-xl">
                <h3 className="font-medium text-navy dark:text-gray-200 mb-2">Import Data</h3>
                <p className="text-sm text-navy-light dark:text-gray-400 mb-4">
                  Restore from a previous backup. Data will be <strong>merged</strong> with existing data (duplicates are skipped).
                </p>
                <div className="flex flex-col sm:flex-row gap-3">
                  <label className="flex-1">
                    <input
                      type="file"
                      accept=".json"
                      className="hidden"
                      data-testid="import-file-input"
                      onChange={async (e) => {
                        const file = e.target.files[0];
                        if (!file) return;
                        if (!file.name.endsWith('.json')) {
                          toast.error('Please select a JSON backup file');
                          return;
                        }
                        setImportLoading(true);
                        try {
                          const response = await importAPI.importData(file);
                          const data = response.data;
                          toast.success(data.message);
                        } catch (error) {
                          const detail = error.response?.data?.detail || 'Failed to import data';
                          toast.error(detail);
                        }
                        setImportLoading(false);
                        e.target.value = '';
                      }}
                    />
                    <Button
                      variant="outline"
                      className="w-full border-sage dark:border-gray-600 cursor-pointer"
                      disabled={importLoading}
                      data-testid="import-data-btn"
                      asChild
                    >
                      <span>
                        {importLoading ? (
                          <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Importing...</>
                        ) : (
                          <><Upload className="w-4 h-4 mr-2" /> Import Backup (JSON)</>
                        )}
                      </span>
                    </Button>
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SettingsPage;
