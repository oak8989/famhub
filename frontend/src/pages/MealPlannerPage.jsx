import React, { useState, useEffect } from 'react';
import { Utensils, Plus, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { mealPlanAPI, recipesAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { format, startOfWeek, addDays, addWeeks, subWeeks } from 'date-fns';

const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack'];

const mealTypeStyles = {
  breakfast: 'bg-sunny/20 text-amber-700 border-sunny',
  lunch: 'bg-sage/20 text-green-700 border-sage',
  dinner: 'bg-terracotta/20 text-terracotta border-terracotta',
  snack: 'bg-purple-100 text-purple-700 border-purple-300'
};

const MealPlannerPage = () => {
  const [mealPlans, setMealPlans] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [weekStart, setWeekStart] = useState(startOfWeek(new Date(), { weekStartsOn: 1 }));
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState('');
  const [form, setForm] = useState({ meal_type: 'dinner', recipe_name: '', recipe_id: '', notes: '' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [plansRes, recipesRes] = await Promise.all([
        mealPlanAPI.getPlans(),
        recipesAPI.getRecipes().catch(() => ({ data: [] }))
      ]);
      setMealPlans(plansRes.data);
      setRecipes(recipesRes.data);
    } catch (error) {
      toast.error('Failed to load meal plans');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.recipe_name.trim()) {
      toast.error('Please enter a meal name');
      return;
    }

    try {
      await mealPlanAPI.createPlan({
        ...form,
        date: selectedDate
      });
      toast.success('Meal planned!');
      setDialogOpen(false);
      setForm({ meal_type: 'dinner', recipe_name: '', recipe_id: '', notes: '' });
      loadData();
    } catch (error) {
      toast.error('Failed to save meal plan');
    }
  };

  const handleDelete = async (id) => {
    try {
      await mealPlanAPI.deletePlan(id);
      loadData();
      toast.success('Meal removed');
    } catch (error) {
      toast.error('Failed to delete meal');
    }
  };

  const openAddDialog = (date) => {
    setSelectedDate(format(date, 'yyyy-MM-dd'));
    setForm({ meal_type: 'dinner', recipe_name: '', recipe_id: '', notes: '' });
    setDialogOpen(true);
  };

  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  const getMealsForDate = (date) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return mealPlans.filter(m => m.date === dateStr);
  };

  return (
    <div className="space-y-6" data-testid="meal-planner-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-navy flex items-center gap-3">
            <Utensils className="w-8 h-8 text-orange-400" />
            Meal Planner
          </h1>
          <p className="text-navy-light mt-1">Plan your family's meals for the week</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setWeekStart(subWeeks(weekStart, 1))}
            className="border-sunny"
            data-testid="prev-week-btn"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-navy font-medium px-4">
            {format(weekStart, 'MMM d')} - {format(addDays(weekStart, 6), 'MMM d, yyyy')}
          </span>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setWeekStart(addWeeks(weekStart, 1))}
            className="border-sunny"
            data-testid="next-week-btn"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Week grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="spinner" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
          {weekDays.map((day) => {
            const isToday = format(day, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');
            const meals = getMealsForDate(day);
            
            return (
              <div
                key={day.toISOString()}
                className={`card-cozy ${isToday ? 'ring-2 ring-terracotta' : ''}`}
                data-testid={`day-${format(day, 'yyyy-MM-dd')}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-xs text-navy-light uppercase">
                      {format(day, 'EEE')}
                    </p>
                    <p className={`font-heading font-bold ${isToday ? 'text-terracotta' : 'text-navy'}`}>
                      {format(day, 'd')}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => openAddDialog(day)}
                    className="h-8 w-8 text-terracotta hover:bg-terracotta/10"
                    data-testid={`add-meal-${format(day, 'yyyy-MM-dd')}`}
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                
                <div className="space-y-2">
                  {meals.length === 0 ? (
                    <p className="text-sm text-navy-light/50 text-center py-4 font-handwritten">
                      No meals planned
                    </p>
                  ) : (
                    meals.map((meal) => (
                      <div
                        key={meal.id}
                        className={`p-2 rounded-lg border ${mealTypeStyles[meal.meal_type]} group relative`}
                        data-testid={`meal-${meal.id}`}
                      >
                        <p className="text-xs font-medium capitalize">{meal.meal_type}</p>
                        <p className="text-sm font-medium truncate">{meal.recipe_name}</p>
                        {meal.notes && (
                          <p className="text-xs opacity-70 truncate">{meal.notes}</p>
                        )}
                        <button
                          onClick={() => handleDelete(meal.id)}
                          className="absolute top-1 right-1 p-1 hover:bg-white/50 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                          data-testid={`delete-meal-${meal.id}`}
                        >
                          <Trash2 className="w-3 h-3 text-red-500" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add meal dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="bg-warm-white border-sunny/50">
          <DialogHeader>
            <DialogTitle className="font-heading text-navy">
              Plan Meal for {selectedDate && format(new Date(selectedDate), 'MMMM d')}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-navy mb-2">Meal Type</label>
              <Select value={form.meal_type} onValueChange={(v) => setForm({ ...form, meal_type: v })}>
                <SelectTrigger className="input-cozy" data-testid="meal-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {mealTypes.map(type => (
                    <SelectItem key={type} value={type} className="capitalize">{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-navy mb-2">Meal Name</label>
              {recipes.length > 0 ? (
                <Select 
                  value={form.recipe_id} 
                  onValueChange={(v) => {
                    const recipe = recipes.find(r => r.id === v);
                    setForm({ ...form, recipe_id: v, recipe_name: recipe?.name || '' });
                  }}
                >
                  <SelectTrigger className="input-cozy" data-testid="recipe-select">
                    <SelectValue placeholder="Select from recipes or type below" />
                  </SelectTrigger>
                  <SelectContent>
                    {recipes.map(recipe => (
                      <SelectItem key={recipe.id} value={recipe.id}>{recipe.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : null}
              <Input
                value={form.recipe_name}
                onChange={(e) => setForm({ ...form, recipe_name: e.target.value, recipe_id: '' })}
                placeholder="Or type a meal name"
                className="input-cozy mt-2"
                data-testid="meal-name-input"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-navy mb-2">Notes</label>
              <Input
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Any special notes?"
                className="input-cozy"
                data-testid="meal-notes-input"
              />
            </div>
            
            <div className="flex gap-3">
              <Button type="submit" className="btn-primary flex-1" data-testid="save-meal-btn">
                Add Meal
              </Button>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="border-sunny">
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MealPlannerPage;
