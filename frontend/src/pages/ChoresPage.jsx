import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import { 
  Award, Plus, Check, Trash2, Gift, Trophy, Star, 
  Calendar, User, Sparkles, Crown, History
} from 'lucide-react';
import api from '../lib/api';

const DIFFICULTY_COLORS = {
  easy: 'bg-green-500',
  medium: 'bg-yellow-500',
  hard: 'bg-red-500',
};

const DIFFICULTY_POINTS = {
  easy: 5,
  medium: 10,
  hard: 20,
};

const formatClaimDate = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${String(d.getDate()).padStart(2,'0')}${months[d.getMonth()]}${d.getFullYear()}`;
};

const ChoresPage = () => {
  const { user } = useAuth();
  const [chores, setChores] = useState([]);
  const [rewards, setRewards] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [members, setMembers] = useState([]);
  const [claimHistory, setClaimHistory] = useState([]);
  const [choreOpen, setChoreOpen] = useState(false);
  const [rewardOpen, setRewardOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newChore, setNewChore] = useState({
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    difficulty: 'medium',
  });
  const [newReward, setNewReward] = useState({
    name: '',
    description: '',
    points_required: 50,
  });

  const isAdmin = user?.role === 'owner' || user?.role === 'parent';

  // Get live user points from leaderboard (auth context is stale)
  const myPoints = leaderboard.find(m => m.id === user?.id)?.points || 0;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [choresRes, rewardsRes, leaderboardRes, membersRes, claimsRes] = await Promise.all([
        api.get('/chores'),
        api.get('/rewards'),
        api.get('/leaderboard'),
        api.get('/family/members'),
        api.get('/reward-claims'),
      ]);
      setChores(choresRes.data || []);
      setRewards(rewardsRes.data || []);
      setLeaderboard(leaderboardRes.data || []);
      setMembers(membersRes.data || []);
      setClaimHistory(claimsRes.data || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateChore = async () => {
    if (!newChore.title) {
      toast.error('Please enter a title');
      return;
    }
    try {
      await api.post('/chores', newChore);
      toast.success('Chore created');
      setChoreOpen(false);
      setNewChore({ title: '', description: '', assigned_to: '', due_date: '', difficulty: 'medium' });
      loadData();
    } catch (error) {
      toast.error('Failed to create chore');
    }
  };

  const handleCompleteChore = async (choreId) => {
    try {
      const res = await api.post(`/chores/${choreId}/complete`);
      toast.success(`Chore completed! +${res.data.points_earned} points`);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete chore');
    }
  };

  const handleDeleteChore = async (choreId) => {
    try {
      await api.delete(`/chores/${choreId}`);
      toast.success('Chore deleted');
      loadData();
    } catch (error) {
      toast.error('Failed to delete chore');
    }
  };

  const handleCreateReward = async () => {
    if (!newReward.name) {
      toast.error('Please enter a reward name');
      return;
    }
    try {
      await api.post('/rewards', newReward);
      toast.success('Reward created');
      setRewardOpen(false);
      setNewReward({ name: '', description: '', points_required: 50 });
      loadData();
    } catch (error) {
      toast.error('Failed to create reward');
    }
  };

  const handleClaimReward = async (rewardId, userId) => {
    try {
      await api.post('/rewards/claim', { reward_id: rewardId, user_id: userId });
      toast.success('Reward claimed!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to claim reward');
    }
  };

  const handleDeleteReward = async (rewardId) => {
    try {
      await api.delete(`/rewards/${rewardId}`);
      toast.success('Reward deleted');
      loadData();
    } catch (error) {
      toast.error('Failed to delete reward');
    }
  };

  const pendingChores = chores.filter(c => !c.completed);
  const completedChores = chores.filter(c => c.completed);
  const myChores = pendingChores.filter(c => c.assigned_to === user?.id);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="chores-page">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Award className="w-8 h-8 text-terracotta" />
          <div>
            <h1 className="text-2xl font-heading font-bold text-navy">Chores & Rewards</h1>
            <p className="text-navy-light">Complete chores, earn points, claim rewards!</p>
          </div>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            <Dialog open={choreOpen} onOpenChange={setChoreOpen}>
              <DialogTrigger asChild>
                <Button data-testid="add-chore-btn">
                  <Plus className="w-4 h-4 mr-2" /> Add Chore
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Chore</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label>Title</Label>
                    <Input
                      value={newChore.title}
                      onChange={(e) => setNewChore({ ...newChore, title: e.target.value })}
                      placeholder="Clean your room"
                      data-testid="chore-title-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      value={newChore.description}
                      onChange={(e) => setNewChore({ ...newChore, description: e.target.value })}
                      placeholder="Details about the chore..."
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Assign To</Label>
                    <Select
                      value={newChore.assigned_to || "anyone"}
                      onValueChange={(value) => setNewChore({ ...newChore, assigned_to: value === "anyone" ? "" : value })}
                    >
                      <SelectTrigger data-testid="chore-assign-select">
                        <SelectValue placeholder="Select member" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="anyone">Anyone</SelectItem>
                        {members.map((m) => (
                          <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Due Date</Label>
                      <Input
                        type="date"
                        value={newChore.due_date}
                        onChange={(e) => setNewChore({ ...newChore, due_date: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Difficulty</Label>
                      <Select
                        value={newChore.difficulty}
                        onValueChange={(value) => setNewChore({ ...newChore, difficulty: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="easy">Easy (5 pts)</SelectItem>
                          <SelectItem value="medium">Medium (10 pts)</SelectItem>
                          <SelectItem value="hard">Hard (20 pts)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <Button onClick={handleCreateChore} className="w-full" data-testid="create-chore-btn">
                    Create Chore
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
            
            <Dialog open={rewardOpen} onOpenChange={setRewardOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" data-testid="add-reward-btn">
                  <Gift className="w-4 h-4 mr-2" /> Add Reward
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Reward</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label>Reward Name</Label>
                    <Input
                      value={newReward.name}
                      onChange={(e) => setNewReward({ ...newReward, name: e.target.value })}
                      placeholder="Extra screen time"
                      data-testid="reward-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      value={newReward.description}
                      onChange={(e) => setNewReward({ ...newReward, description: e.target.value })}
                      placeholder="30 minutes of extra screen time"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Points Required</Label>
                    <Input
                      type="number"
                      value={newReward.points_required}
                      onChange={(e) => setNewReward({ ...newReward, points_required: parseInt(e.target.value) || 0 })}
                      data-testid="reward-points-input"
                    />
                  </div>
                  <Button onClick={handleCreateReward} className="w-full" data-testid="create-reward-btn">
                    Create Reward
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="card-base">
          <CardContent className="p-4 text-center">
            <Star className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-navy" data-testid="user-points">{myPoints}</p>
            <p className="text-sm text-navy-light">Your Points</p>
          </CardContent>
        </Card>
        <Card className="card-base">
          <CardContent className="p-4 text-center">
            <Check className="w-8 h-8 text-green-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-navy">{completedChores.length}</p>
            <p className="text-sm text-navy-light">Completed</p>
          </CardContent>
        </Card>
        <Card className="card-base">
          <CardContent className="p-4 text-center">
            <Award className="w-8 h-8 text-terracotta mx-auto mb-2" />
            <p className="text-2xl font-bold text-navy">{pendingChores.length}</p>
            <p className="text-sm text-navy-light">Pending</p>
          </CardContent>
        </Card>
        <Card className="card-base">
          <CardContent className="p-4 text-center">
            <Gift className="w-8 h-8 text-purple-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-navy">{rewards.length}</p>
            <p className="text-sm text-navy-light">Rewards</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="chores" className="space-y-4">
        <TabsList className="bg-warm-white">
          <TabsTrigger value="chores" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
            Chores
          </TabsTrigger>
          <TabsTrigger value="rewards" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
            Rewards
          </TabsTrigger>
          <TabsTrigger value="leaderboard" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
            Leaderboard
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
            History
          </TabsTrigger>
        </TabsList>

        {/* Chores Tab */}
        <TabsContent value="chores" className="space-y-4">
          {myChores.length > 0 && (
            <Card className="card-base border-2 border-terracotta">
              <CardHeader>
                <CardTitle className="text-navy flex items-center gap-2">
                  <User className="w-5 h-5" /> Your Chores
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {myChores.map((chore) => (
                  <ChoreCard
                    key={chore.id}
                    chore={chore}
                    onComplete={handleCompleteChore}
                    onDelete={handleDeleteChore}
                    isAdmin={isAdmin}
                    isMine={true}
                  />
                ))}
              </CardContent>
            </Card>
          )}

          <Card className="card-base">
            <CardHeader>
              <CardTitle className="text-navy">All Chores</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {pendingChores.length === 0 ? (
                <p className="text-center text-navy-light py-8">
                  <Sparkles className="w-12 h-12 mx-auto mb-2 text-sunny" />
                  No pending chores! Great job!
                </p>
              ) : (
                pendingChores.map((chore) => (
                  <ChoreCard
                    key={chore.id}
                    chore={chore}
                    onComplete={handleCompleteChore}
                    onDelete={handleDeleteChore}
                    isAdmin={isAdmin}
                    isMine={chore.assigned_to === user?.id}
                  />
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rewards Tab */}
        <TabsContent value="rewards" className="space-y-4">
          <Card className="card-base">
            <CardHeader>
              <CardTitle className="text-navy">Available Rewards</CardTitle>
            </CardHeader>
            <CardContent>
              {rewards.length === 0 ? (
                <p className="text-center text-navy-light py-8">
                  <Gift className="w-12 h-12 mx-auto mb-2 text-purple-300" />
                  No rewards yet. {isAdmin ? 'Create some rewards!' : 'Ask a parent to add rewards!'}
                </p>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {rewards.map((reward) => (
                    <div
                      key={reward.id}
                      className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border border-purple-200"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-medium text-navy flex items-center gap-2">
                            <Gift className="w-5 h-5 text-purple-500" />
                            {reward.name}
                          </h3>
                          {reward.description && (
                            <p className="text-sm text-navy-light mt-1">{reward.description}</p>
                          )}
                        </div>
                        {isAdmin && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteReward(reward.id)}
                            className="text-red-500"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                      <div className="mt-4 flex items-center justify-between">
                        <Badge className="bg-purple-500 text-white">
                          <Star className="w-3 h-3 mr-1" /> {reward.points_required} pts
                        </Badge>
                        <Button
                          size="sm"
                          disabled={myPoints < reward.points_required}
                          onClick={() => handleClaimReward(reward.id, user?.id)}
                          data-testid={`claim-reward-${reward.id}`}
                        >
                          {myPoints >= reward.points_required ? 'Claim' : 'Need more points'}
                        </Button>
                      </div>
                      {myPoints < reward.points_required && (
                        <Progress
                          value={(myPoints / reward.points_required) * 100}
                          className="mt-2 h-2"
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard">
          <Card className="card-base">
            <CardHeader>
              <CardTitle className="text-navy flex items-center gap-2">
                <Trophy className="w-5 h-5 text-yellow-500" /> Family Leaderboard
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {leaderboard.map((member, index) => (
                  <div
                    key={member.id}
                    className={`flex items-center justify-between p-4 rounded-xl ${
                      index === 0 ? 'bg-gradient-to-r from-yellow-100 to-amber-100 border-2 border-yellow-400' :
                      index === 1 ? 'bg-gradient-to-r from-gray-100 to-slate-100 border border-gray-300' :
                      index === 2 ? 'bg-gradient-to-r from-orange-100 to-amber-100 border border-orange-300' :
                      'bg-cream'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                        index === 0 ? 'bg-yellow-500 text-white' :
                        index === 1 ? 'bg-gray-400 text-white' :
                        index === 2 ? 'bg-orange-400 text-white' :
                        'bg-navy-light text-white'
                      }`}>
                        {index + 1}
                      </div>
                      <Avatar className="w-10 h-10">
                        <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${member.avatar_seed}`} />
                        <AvatarFallback>{member.name?.charAt(0)}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium text-navy flex items-center gap-2">
                          {member.name}
                          {index === 0 && <Crown className="w-4 h-4 text-yellow-500" />}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Star className="w-5 h-5 text-yellow-500" />
                      <span className="font-bold text-navy">{member.points || 0}</span>
                      <span className="text-sm text-navy-light">pts</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab - Claimed Rewards */}
        <TabsContent value="history" className="space-y-4" data-testid="claims-history-tab">
          <Card className="card-base">
            <CardHeader>
              <CardTitle className="text-navy flex items-center gap-2">
                <History className="w-5 h-5 text-terracotta" /> Claimed Rewards
              </CardTitle>
            </CardHeader>
            <CardContent>
              {claimHistory.length === 0 ? (
                <p className="text-center text-navy-light py-6">No rewards claimed yet</p>
              ) : (
                <div className="space-y-2">
                  {claimHistory.map((claim, i) => (
                    <div key={claim.id || i} className="flex items-center justify-between p-3 bg-cream dark:bg-gray-700/50 rounded-xl" data-testid={`claim-row-${i}`}>
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center">
                          <Gift className="w-4 h-4 text-amber-600" />
                        </div>
                        <div>
                          <p className="font-medium text-navy dark:text-gray-200 text-sm">{claim.reward_name}</p>
                          <p className="text-xs text-navy-light dark:text-gray-400">
                            Claimed by <span className="font-semibold">{claim.user_name}</span>
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-terracotta">{claim.points_spent} pts</p>
                        <p className="text-xs text-navy-light dark:text-gray-400">{formatClaimDate(claim.claimed_at)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const ChoreCard = ({ chore, onComplete, onDelete, isAdmin, isMine }) => (
  <div
    className={`p-4 rounded-xl ${isMine ? 'bg-terracotta/10 border border-terracotta/30' : 'bg-cream'}`}
    data-testid={`chore-${chore.id}`}
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="font-medium text-navy">{chore.title}</h3>
          <Badge className={`${DIFFICULTY_COLORS[chore.difficulty]} text-white text-xs`}>
            {chore.difficulty} • {chore.points} pts
          </Badge>
        </div>
        {chore.description && (
          <p className="text-sm text-navy-light">{chore.description}</p>
        )}
        <div className="flex items-center gap-4 mt-2 text-sm text-navy-light">
          {chore.assigned_to_name && (
            <span className="flex items-center gap-1">
              <User className="w-4 h-4" /> {chore.assigned_to_name}
            </span>
          )}
          {chore.due_date && (
            <span className="flex items-center gap-1">
              <Calendar className="w-4 h-4" /> {new Date(chore.due_date).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
      <div className="flex gap-2">
        {!chore.completed && (isMine || !chore.assigned_to || isAdmin) && (
          <Button
            size="sm"
            onClick={() => onComplete(chore.id)}
            className="bg-green-500 hover:bg-green-600"
            data-testid={`complete-chore-${chore.id}`}
          >
            <Check className="w-4 h-4" />
          </Button>
        )}
        {isAdmin && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onDelete(chore.id)}
            className="text-red-500 hover:text-red-600 hover:bg-red-50"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        )}
      </div>
    </div>
  </div>
);

export default ChoresPage;
