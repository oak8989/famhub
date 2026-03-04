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
  Settings, Users, Shield, Palette, Calendar, UserPlus, Trash2, 
  RefreshCw, Mail, Server, Check, X, Crown, Eye, EyeOff, Copy
} from 'lucide-react';
import api from '../lib/api';

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
  const { user, family, loadFamily } = useAuth();
  const [searchParams] = useSearchParams();
  const [members, setMembers] = useState([]);
  const [settings, setSettings] = useState(null);
  const [familyName, setFamilyName] = useState('');
  const [familyPin, setFamilyPin] = useState('');
  const [showPin, setShowPin] = useState(false);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteData, setInviteData] = useState({ name: '', email: '', role: 'member' });
  const [loading, setLoading] = useState(true);

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
        api.get('/api/family/members'),
        api.get('/api/settings'),
        api.get('/api/family'),
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
      await api.put('/api/family', { name: familyName });
      toast.success('Family name updated');
      loadFamily();
    } catch (error) {
      toast.error('Failed to update family name');
    }
  };

  const handleRegenerateFamilyPin = async () => {
    try {
      const res = await api.post('/api/family/regenerate-pin');
      setFamilyPin(res.data.pin);
      toast.success('Family PIN regenerated');
    } catch (error) {
      toast.error('Failed to regenerate PIN');
    }
  };

  const handleInviteMember = async () => {
    if (!inviteData.name || !inviteData.email) {
      toast.error('Please fill in all fields');
      return;
    }
    try {
      const res = await api.post('/api/family/invite', inviteData);
      toast.success(`Invitation sent! User PIN: ${res.data.user_pin}`);
      setInviteOpen(false);
      setInviteData({ name: '', email: '', role: 'member' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to invite member');
    }
  };

  const handleUpdateRole = async (memberId, newRole) => {
    try {
      await api.put(`/api/family/members/${memberId}/role`, { role: newRole });
      toast.success('Role updated');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;
    try {
      await api.delete(`/api/family/members/${memberId}`);
      toast.success('Member removed');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to remove member');
    }
  };

  const handleRegenerateUserPin = async (memberId) => {
    try {
      const res = await api.post(`/api/family/members/${memberId}/regenerate-pin`);
      toast.success(`New PIN: ${res.data.pin}`);
      loadData();
    } catch (error) {
      toast.error('Failed to regenerate PIN');
    }
  };

  const handleModuleToggle = async (module, enabled) => {
    const newSettings = { ...settings };
    newSettings.modules[module].enabled = enabled;
    setSettings(newSettings);
    try {
      await api.put('/api/settings', { modules: newSettings.modules });
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
      await api.put('/api/settings', { modules: newSettings.modules });
    } catch (error) {
      toast.error('Failed to save settings');
    }
  };

  const handleConnectGoogle = async () => {
    try {
      const res = await api.get('/api/calendar/google/auth');
      window.location.href = res.data.authorization_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Google Calendar not configured');
    }
  };

  const handleDisconnectGoogle = async () => {
    try {
      await api.delete('/api/calendar/google/disconnect');
      toast.success('Google Calendar disconnected');
      loadData();
    } catch (error) {
      toast.error('Failed to disconnect');
    }
  };

  const handleSyncGoogle = async () => {
    try {
      const res = await api.post('/api/calendar/google/sync');
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
        <TabsList className="bg-warm-white">
          <TabsTrigger value="family" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
            <Users className="w-4 h-4 mr-2" /> Family
          </TabsTrigger>
          {isAdmin && (
            <>
              <TabsTrigger value="modules" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
                <Shield className="w-4 h-4 mr-2" /> Modules
              </TabsTrigger>
              <TabsTrigger value="integrations" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
                <Calendar className="w-4 h-4 mr-2" /> Integrations
              </TabsTrigger>
            </>
          )}
          {isOwner && (
            <TabsTrigger value="server" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
              <Server className="w-4 h-4 mr-2" /> Server
            </TabsTrigger>
          )}
        </TabsList>

        {/* Family Tab */}
        <TabsContent value="family" className="space-y-4">
          {/* Family Info */}
          <Card className="card-base">
            <CardHeader>
              <CardTitle className="text-navy">Family Information</CardTitle>
              <CardDescription>Manage your family details</CardDescription>
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
                  <Label>Family PIN</Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Input
                        type={showPin ? 'text' : 'password'}
                        value={familyPin}
                        readOnly
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
                      <Button variant="outline" onClick={handleRegenerateFamilyPin} data-testid="regenerate-pin-btn">
                        <RefreshCw className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Members */}
          <Card className="card-base">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-navy">Family Members</CardTitle>
                <CardDescription>Manage who has access</CardDescription>
              </div>
              {isAdmin && (
                <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
                  <DialogTrigger asChild>
                    <Button data-testid="invite-member-btn">
                      <UserPlus className="w-4 h-4 mr-2" /> Invite Member
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Invite Family Member</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 pt-4">
                      <div className="space-y-2">
                        <Label>Name</Label>
                        <Input
                          value={inviteData.name}
                          onChange={(e) => setInviteData({ ...inviteData, name: e.target.value })}
                          placeholder="John Doe"
                          data-testid="invite-name-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Email</Label>
                        <Input
                          type="email"
                          value={inviteData.email}
                          onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
                          placeholder="john@example.com"
                          data-testid="invite-email-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Role</Label>
                        <Select
                          value={inviteData.role}
                          onValueChange={(value) => setInviteData({ ...inviteData, role: value })}
                        >
                          <SelectTrigger data-testid="invite-role-select">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="parent">Parent</SelectItem>
                            <SelectItem value="member">Family Member</SelectItem>
                            <SelectItem value="child">Child</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button onClick={handleInviteMember} className="w-full" data-testid="send-invite-btn">
                        <Mail className="w-4 h-4 mr-2" /> Send Invitation
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              )}
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {members.map((member) => (
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
                        <span className="text-sm text-navy-light">{member.email}</span>
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
                          <SelectTrigger className="w-32">
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
                            onClick={() => handleRegenerateUserPin(member.id)}
                            title="Regenerate PIN"
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
                ))}
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
                  <Button onClick={handleConnectGoogle} data-testid="connect-google-btn">
                    <Calendar className="w-4 h-4 mr-2" /> Connect Google Calendar
                  </Button>
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
                <CardDescription>These settings are configured in your server's .env file</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-cream rounded-xl">
                  <h3 className="font-medium text-navy mb-2">SMTP Email Settings</h3>
                  <p className="text-sm text-navy-light mb-4">
                    Configure these in your backend/.env file to enable email invitations:
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
                  <h3 className="font-medium text-navy mb-2">Google Calendar Integration</h3>
                  <p className="text-sm text-navy-light mb-4">
                    To enable Google Calendar sync, add these to your backend/.env:
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
      </Tabs>
    </div>
  );
};

export default SettingsPage;
