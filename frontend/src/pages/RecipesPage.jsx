import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, Trash2, Edit2, Clock, Users, Eye } from 'lucide-react';
import { recipesAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';

const categories = ['Breakfast', 'Main Course', 'Side Dish', 'Soup', 'Salad', 'Dessert', 'Snack', 'Beverage'];

const RecipesPage = () => {
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [editingRecipe, setEditingRecipe] = useState(null);
  const [viewingRecipe, setViewingRecipe] = useState(null);
  const [filterCategory, setFilterCategory] = useState('all');
  const [form, setForm] = useState({
    name: '',
    description: '',
    ingredients: '',
    instructions: '',
    prep_time: '',
    cook_time: '',
    servings: 4,
    category: 'Main Course',
    image_url: ''
  });

  useEffect(() => {
    loadRecipes();
  }, []);

  const loadRecipes = async () => {
    try {
      const response = await recipesAPI.getRecipes();
      setRecipes(response.data);
    } catch (error) {
      toast.error('Failed to load recipes');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      toast.error('Please enter a recipe name');
      return;
    }

    try {
      const recipeData = {
        ...form,
        ingredients: form.ingredients.split('\n').filter(i => i.trim()),
        instructions: form.instructions.split('\n').filter(i => i.trim()),
        servings: parseInt(form.servings) || 4
      };

      if (editingRecipe) {
        await recipesAPI.updateRecipe(editingRecipe.id, { ...recipeData, id: editingRecipe.id });
        toast.success('Recipe updated!');
      } else {
        await recipesAPI.createRecipe(recipeData);
        toast.success('Recipe added!');
      }
      
      setDialogOpen(false);
      resetForm();
      loadRecipes();
    } catch (error) {
      toast.error('Failed to save recipe');
    }
  };

  const handleDelete = async (id) => {
    try {
      await recipesAPI.deleteRecipe(id);
      loadRecipes();
      toast.success('Recipe deleted');
    } catch (error) {
      toast.error('Failed to delete recipe');
    }
  };

  const resetForm = () => {
    setEditingRecipe(null);
    setForm({
      name: '',
      description: '',
      ingredients: '',
      instructions: '',
      prep_time: '',
      cook_time: '',
      servings: 4,
      category: 'Main Course',
      image_url: ''
    });
  };

  const openEditDialog = (recipe) => {
    setEditingRecipe(recipe);
    setForm({
      name: recipe.name,
      description: recipe.description || '',
      ingredients: recipe.ingredients?.join('\n') || '',
      instructions: recipe.instructions?.join('\n') || '',
      prep_time: recipe.prep_time || '',
      cook_time: recipe.cook_time || '',
      servings: recipe.servings || 4,
      category: recipe.category || 'Main Course',
      image_url: recipe.image_url || ''
    });
    setDialogOpen(true);
  };

  const filteredRecipes = filterCategory === 'all' 
    ? recipes 
    : recipes.filter(r => r.category === filterCategory);

  return (
    <div className="space-y-6" data-testid="recipes-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-navy flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-pink-400" />
            Recipe Box
          </h1>
          <p className="text-navy-light mt-1">{recipes.length} family recipes</p>
        </div>
        
        <div className="flex gap-3">
          <Select value={filterCategory} onValueChange={setFilterCategory}>
            <SelectTrigger className="w-40 input-cozy" data-testid="category-filter">
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {categories.map(cat => (
                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="btn-primary" data-testid="add-recipe-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Recipe
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-warm-white border-sunny/50 max-w-2xl max-h-[90vh]">
              <DialogHeader>
                <DialogTitle className="font-heading text-navy">
                  {editingRecipe ? 'Edit Recipe' : 'New Recipe'}
                </DialogTitle>
              </DialogHeader>
              <ScrollArea className="max-h-[70vh] pr-4">
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-navy mb-2">Recipe Name</label>
                      <Input
                        value={form.name}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        placeholder="Grandma's Apple Pie"
                        className="input-cozy"
                        data-testid="recipe-name-input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy mb-2">Category</label>
                      <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                        <SelectTrigger className="input-cozy" data-testid="recipe-category-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map(cat => (
                            <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-navy mb-2">Description</label>
                    <Input
                      value={form.description}
                      onChange={(e) => setForm({ ...form, description: e.target.value })}
                      placeholder="A family favorite..."
                      className="input-cozy"
                      data-testid="recipe-description-input"
                    />
                  </div>
                  
                  <div className="grid sm:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-navy mb-2">Prep Time</label>
                      <Input
                        value={form.prep_time}
                        onChange={(e) => setForm({ ...form, prep_time: e.target.value })}
                        placeholder="15 mins"
                        className="input-cozy"
                        data-testid="recipe-prep-input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy mb-2">Cook Time</label>
                      <Input
                        value={form.cook_time}
                        onChange={(e) => setForm({ ...form, cook_time: e.target.value })}
                        placeholder="30 mins"
                        className="input-cozy"
                        data-testid="recipe-cook-input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy mb-2">Servings</label>
                      <Input
                        type="number"
                        value={form.servings}
                        onChange={(e) => setForm({ ...form, servings: e.target.value })}
                        className="input-cozy"
                        data-testid="recipe-servings-input"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-navy mb-2">
                      Ingredients (one per line)
                    </label>
                    <Textarea
                      value={form.ingredients}
                      onChange={(e) => setForm({ ...form, ingredients: e.target.value })}
                      placeholder="2 cups flour&#10;1 cup sugar&#10;3 eggs"
                      className="input-cozy min-h-[120px]"
                      data-testid="recipe-ingredients-input"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-navy mb-2">
                      Instructions (one step per line)
                    </label>
                    <Textarea
                      value={form.instructions}
                      onChange={(e) => setForm({ ...form, instructions: e.target.value })}
                      placeholder="Preheat oven to 350°F&#10;Mix dry ingredients&#10;Add wet ingredients"
                      className="input-cozy min-h-[120px]"
                      data-testid="recipe-instructions-input"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-navy mb-2">Image URL (optional)</label>
                    <Input
                      value={form.image_url}
                      onChange={(e) => setForm({ ...form, image_url: e.target.value })}
                      placeholder="https://..."
                      className="input-cozy"
                      data-testid="recipe-image-input"
                    />
                  </div>
                  
                  <div className="flex gap-3 pt-4">
                    <Button type="submit" className="btn-primary flex-1" data-testid="save-recipe-btn">
                      {editingRecipe ? 'Update' : 'Save'} Recipe
                    </Button>
                    <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="border-sunny">
                      Cancel
                    </Button>
                  </div>
                </form>
              </ScrollArea>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Recipes grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="spinner" />
        </div>
      ) : filteredRecipes.length === 0 ? (
        <div className="card-cozy text-center py-12">
          <BookOpen className="w-16 h-16 text-sunny mx-auto mb-4" />
          <h3 className="text-xl font-heading font-bold text-navy mb-2">No recipes yet</h3>
          <p className="text-navy-light font-handwritten text-lg">Add your family's favorite recipes!</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredRecipes.map((recipe) => (
            <div
              key={recipe.id}
              className="card-cozy group cursor-pointer"
              data-testid={`recipe-${recipe.id}`}
            >
              {recipe.image_url && (
                <div className="h-40 -mx-6 -mt-6 mb-4 rounded-t-3xl overflow-hidden">
                  <img
                    src={recipe.image_url}
                    alt={recipe.name}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <span className="text-xs text-terracotta font-medium">{recipe.category}</span>
                  <h3 className="font-heading font-bold text-navy text-lg truncate">{recipe.name}</h3>
                  {recipe.description && (
                    <p className="text-sm text-navy-light mt-1 line-clamp-2">{recipe.description}</p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-4 mt-3 text-sm text-navy-light">
                {recipe.prep_time && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {recipe.prep_time}
                  </span>
                )}
                {recipe.servings && (
                  <span className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    {recipe.servings}
                  </span>
                )}
              </div>
              
              <div className="flex gap-2 mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => { setViewingRecipe(recipe); setViewDialogOpen(true); }}
                  className="flex-1 text-sage hover:bg-sage/10"
                  data-testid={`view-recipe-${recipe.id}`}
                >
                  <Eye className="w-4 h-4 mr-1" />
                  View
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => openEditDialog(recipe)}
                  className="text-terracotta hover:bg-terracotta/10"
                  data-testid={`edit-recipe-${recipe.id}`}
                >
                  <Edit2 className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(recipe.id)}
                  className="text-red-500 hover:bg-red-50"
                  data-testid={`delete-recipe-${recipe.id}`}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* View recipe dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="bg-warm-white border-sunny/50 max-w-2xl max-h-[90vh]">
          {viewingRecipe && (
            <>
              <DialogHeader>
                <DialogTitle className="font-heading text-navy text-2xl">
                  {viewingRecipe.name}
                </DialogTitle>
              </DialogHeader>
              <ScrollArea className="max-h-[70vh] pr-4">
                <div className="space-y-6">
                  {viewingRecipe.image_url && (
                    <img
                      src={viewingRecipe.image_url}
                      alt={viewingRecipe.name}
                      className="w-full h-48 object-cover rounded-2xl"
                    />
                  )}
                  
                  <div className="flex flex-wrap gap-4 text-sm">
                    <span className="badge-terracotta">{viewingRecipe.category}</span>
                    {viewingRecipe.prep_time && (
                      <span className="flex items-center gap-1 text-navy-light">
                        <Clock className="w-4 h-4" />
                        Prep: {viewingRecipe.prep_time}
                      </span>
                    )}
                    {viewingRecipe.cook_time && (
                      <span className="flex items-center gap-1 text-navy-light">
                        <Clock className="w-4 h-4" />
                        Cook: {viewingRecipe.cook_time}
                      </span>
                    )}
                    {viewingRecipe.servings && (
                      <span className="flex items-center gap-1 text-navy-light">
                        <Users className="w-4 h-4" />
                        Serves {viewingRecipe.servings}
                      </span>
                    )}
                  </div>
                  
                  {viewingRecipe.description && (
                    <p className="text-navy-light">{viewingRecipe.description}</p>
                  )}
                  
                  <div>
                    <h4 className="font-heading font-bold text-navy mb-2">Ingredients</h4>
                    <ul className="space-y-1">
                      {viewingRecipe.ingredients?.map((ing, i) => (
                        <li key={i} className="flex items-start gap-2 text-navy">
                          <span className="w-2 h-2 bg-sage rounded-full mt-2 flex-shrink-0" />
                          {ing}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-heading font-bold text-navy mb-2">Instructions</h4>
                    <ol className="space-y-2">
                      {viewingRecipe.instructions?.map((step, i) => (
                        <li key={i} className="flex gap-3 text-navy">
                          <span className="w-6 h-6 bg-terracotta text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold">
                            {i + 1}
                          </span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>
              </ScrollArea>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RecipesPage;
