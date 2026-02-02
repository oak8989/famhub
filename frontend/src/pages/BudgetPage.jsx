import React, { useState, useEffect } from 'react';
import { DollarSign, Plus, Trash2, TrendingUp, TrendingDown, PiggyBank } from 'lucide-react';
import { budgetAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const categories = {
  income: ['Salary', 'Freelance', 'Investments', 'Gifts', 'Other Income'],
  expense: ['Groceries', 'Utilities', 'Rent', 'Transportation', 'Entertainment', 'Healthcare', 'Education', 'Shopping', 'Dining', 'Other']
};

const BudgetPage = () => {
  const [entries, setEntries] = useState([]);
  const [summary, setSummary] = useState({ income: 0, expenses: 0, balance: 0 });
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    description: '',
    amount: '',
    category: '',
    type: 'expense',
    date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [entriesRes, summaryRes] = await Promise.all([
        budgetAPI.getEntries(),
        budgetAPI.getSummary()
      ]);
      setEntries(entriesRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      toast.error('Failed to load budget data');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.description.trim() || !form.amount) {
      toast.error('Please fill all required fields');
      return;
    }

    try {
      await budgetAPI.createEntry({
        ...form,
        amount: parseFloat(form.amount)
      });
      toast.success('Entry added!');
      setDialogOpen(false);
      setForm({
        description: '',
        amount: '',
        category: '',
        type: 'expense',
        date: new Date().toISOString().split('T')[0]
      });
      loadData();
    } catch (error) {
      toast.error('Failed to add entry');
    }
  };

  const handleDelete = async (id) => {
    try {
      await budgetAPI.deleteEntry(id);
      loadData();
      toast.success('Entry deleted');
    } catch (error) {
      toast.error('Failed to delete entry');
    }
  };

  // Group entries by month
  const groupedEntries = entries.reduce((acc, entry) => {
    const month = entry.date.substring(0, 7);
    if (!acc[month]) acc[month] = [];
    acc[month].push(entry);
    return acc;
  }, {});

  return (
    <div className="space-y-6" data-testid="budget-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-navy flex items-center gap-3">
            <DollarSign className="w-8 h-8 text-green-500" />
            Family Budget
          </h1>
          <p className="text-navy-light mt-1">Track your family finances</p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-primary" data-testid="add-entry-btn">
              <Plus className="w-4 h-4 mr-2" />
              Add Entry
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-warm-white border-sunny/50">
            <DialogHeader>
              <DialogTitle className="font-heading text-navy">Add Budget Entry</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Tabs value={form.type} onValueChange={(v) => setForm({ ...form, type: v, category: '' })}>
                <TabsList className="grid w-full grid-cols-2 bg-cream">
                  <TabsTrigger value="income" className="data-[state=active]:bg-green-500 data-[state=active]:text-white">
                    <TrendingUp className="w-4 h-4 mr-2" />
                    Income
                  </TabsTrigger>
                  <TabsTrigger value="expense" className="data-[state=active]:bg-terracotta data-[state=active]:text-white">
                    <TrendingDown className="w-4 h-4 mr-2" />
                    Expense
                  </TabsTrigger>
                </TabsList>
              </Tabs>
              
              <div>
                <label className="block text-sm font-medium text-navy mb-2">Description</label>
                <Input
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="What was it for?"
                  className="input-cozy"
                  data-testid="budget-description-input"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-navy mb-2">Amount</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: e.target.value })}
                    placeholder="0.00"
                    className="input-cozy"
                    data-testid="budget-amount-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-navy mb-2">Category</label>
                  <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                    <SelectTrigger className="input-cozy" data-testid="budget-category-select">
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories[form.type].map(cat => (
                        <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-navy mb-2">Date</label>
                <Input
                  type="date"
                  value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                  className="input-cozy"
                  data-testid="budget-date-input"
                />
              </div>
              
              <div className="flex gap-3">
                <Button type="submit" className="btn-primary flex-1" data-testid="save-budget-btn">
                  Add Entry
                </Button>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="border-sunny">
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary cards */}
      <div className="grid sm:grid-cols-3 gap-4">
        <div className="card-cozy bg-green-50 border-green-200">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-green-700">Total Income</p>
              <p className="text-2xl font-heading font-bold text-green-600">
                ${summary.income.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
        
        <div className="card-cozy bg-red-50 border-red-200">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
              <TrendingDown className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <p className="text-sm text-red-600">Total Expenses</p>
              <p className="text-2xl font-heading font-bold text-red-500">
                ${summary.expenses.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
        
        <div className={`card-cozy ${summary.balance >= 0 ? 'bg-sage/10 border-sage/30' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${summary.balance >= 0 ? 'bg-sage/20' : 'bg-red-100'}`}>
              <PiggyBank className={`w-6 h-6 ${summary.balance >= 0 ? 'text-sage' : 'text-red-500'}`} />
            </div>
            <div>
              <p className={`text-sm ${summary.balance >= 0 ? 'text-sage' : 'text-red-600'}`}>Balance</p>
              <p className={`text-2xl font-heading font-bold ${summary.balance >= 0 ? 'text-sage' : 'text-red-500'}`}>
                ${Math.abs(summary.balance).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Entries list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="spinner" />
        </div>
      ) : entries.length === 0 ? (
        <div className="card-cozy text-center py-12">
          <DollarSign className="w-16 h-16 text-sunny mx-auto mb-4" />
          <h3 className="text-xl font-heading font-bold text-navy mb-2">No entries yet</h3>
          <p className="text-navy-light font-handwritten text-lg">Start tracking your budget!</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedEntries)
            .sort(([a], [b]) => b.localeCompare(a))
            .map(([month, monthEntries]) => (
              <div key={month} className="card-cozy">
                <h2 className="font-heading font-bold text-navy mb-4">
                  {new Date(month + '-01').toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </h2>
                <div className="space-y-2">
                  {monthEntries.sort((a, b) => b.date.localeCompare(a.date)).map((entry) => (
                    <div
                      key={entry.id}
                      className={`flex items-center gap-4 p-3 rounded-xl ${
                        entry.type === 'income' ? 'bg-green-50' : 'bg-red-50'
                      } group`}
                      data-testid={`budget-entry-${entry.id}`}
                    >
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        entry.type === 'income' ? 'bg-green-100' : 'bg-red-100'
                      }`}>
                        {entry.type === 'income' ? (
                          <TrendingUp className="w-5 h-5 text-green-600" />
                        ) : (
                          <TrendingDown className="w-5 h-5 text-red-500" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-navy">{entry.description}</p>
                        <p className="text-sm text-navy-light">
                          {entry.category} • {entry.date}
                        </p>
                      </div>
                      <p className={`font-heading font-bold ${
                        entry.type === 'income' ? 'text-green-600' : 'text-red-500'
                      }`}>
                        {entry.type === 'income' ? '+' : '-'}${entry.amount.toFixed(2)}
                      </p>
                      <button
                        onClick={() => handleDelete(entry.id)}
                        className="p-2 hover:bg-white/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                        data-testid={`delete-budget-${entry.id}`}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
};

export default BudgetPage;
