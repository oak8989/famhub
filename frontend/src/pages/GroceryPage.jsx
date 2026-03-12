import React, { useState, useEffect } from 'react';
import { List, Plus, Trash2, Check } from 'lucide-react';
import { groceryAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Checkbox } from '../components/ui/checkbox';

const GroceryPage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newItem, setNewItem] = useState({ name: '', quantity: '' });

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    try {
      const response = await groceryAPI.getItems();
      setItems(response.data);
    } catch (error) {
      toast.error('Failed to load grocery list');
    }
    setLoading(false);
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newItem.name.trim()) return;

    try {
      await groceryAPI.createItem(newItem);
      setNewItem({ name: '', quantity: '' });
      loadItems();
      toast.success('Added!');
    } catch (error) {
      toast.error('Failed to add item');
    }
  };

  const handleToggle = async (item) => {
    try {
      await groceryAPI.updateItem(item.id, { ...item, checked: !item.checked });
      loadItems();
    } catch (error) {
      toast.error('Failed to update item');
    }
  };

  const handleDelete = async (id) => {
    try {
      await groceryAPI.deleteItem(id);
      loadItems();
    } catch (error) {
      toast.error('Failed to delete item');
    }
  };

  const handleClearChecked = async () => {
    try {
      await groceryAPI.clearChecked();
      loadItems();
      toast.success('Checked items cleared');
    } catch (error) {
      toast.error('Failed to clear items');
    }
  };

  const uncheckedItems = items.filter(i => !i.checked);
  const checkedItems = items.filter(i => i.checked);

  return (
    <div className="space-y-6 max-w-2xl mx-auto" data-testid="grocery-page">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-teal-100 rounded-2xl mb-4">
          <List className="w-8 h-8 text-teal-500" />
        </div>
        <h1 className="text-3xl font-heading font-bold text-navy">Quick Grocery List</h1>
        <p className="text-navy-light mt-1">Fast and simple grocery tracking</p>
      </div>

      {/* Add item */}
      <form onSubmit={handleAdd} className="card-cozy">
        <div className="flex gap-3">
          <Input
            value={newItem.name}
            onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
            placeholder="Add item..."
            className="input-cozy flex-1"
            data-testid="grocery-input"
          />
          <Input
            value={newItem.quantity}
            onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
            placeholder="0"
            className="input-cozy w-20"
            data-testid="grocery-quantity"
          />
          <Button type="submit" className="btn-primary" data-testid="add-grocery-btn">
            <Plus className="w-4 h-4" />
          </Button>
        </div>
      </form>

      {/* Items */}
      {loading ? (
        <div className="flex justify-center py-8">
          <div className="spinner" />
        </div>
      ) : items.length === 0 ? (
        <div className="card-cozy text-center py-8">
          <List className="w-12 h-12 text-sunny mx-auto mb-3" />
          <p className="text-navy-light font-handwritten text-lg">Your list is empty!</p>
        </div>
      ) : (
        <>
          {/* Unchecked items */}
          {uncheckedItems.length > 0 && (
            <div className="card-cozy">
              <h2 className="font-heading font-bold text-navy mb-4">To Get ({uncheckedItems.length})</h2>
              <div className="space-y-2">
                {uncheckedItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-3 p-3 rounded-xl bg-cream hover:bg-sunny/20 transition-colors"
                    data-testid={`grocery-item-${item.id}`}
                  >
                    <Checkbox
                      checked={false}
                      onCheckedChange={() => handleToggle(item)}
                      className="border-teal-400 data-[state=checked]:bg-teal-500"
                      data-testid={`grocery-check-${item.id}`}
                    />
                    <span className="flex-1 text-navy">{item.name}</span>
                    {item.quantity !== '1' && (
                      <span className="text-sm text-navy-light bg-sunny/30 px-2 py-1 rounded">
                        {item.quantity}
                      </span>
                    )}
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="p-1 hover:bg-red-100 rounded"
                      data-testid={`grocery-delete-${item.id}`}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Checked items */}
          {checkedItems.length > 0 && (
            <div className="card-cozy bg-sage/5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-heading font-bold text-navy">Done ({checkedItems.length})</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearChecked}
                  className="text-red-500 hover:bg-red-50"
                  data-testid="clear-grocery-btn"
                >
                  <Trash2 className="w-4 h-4 mr-1" />
                  Clear
                </Button>
              </div>
              <div className="space-y-2">
                {checkedItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-3 p-3 rounded-xl bg-sage/10"
                    data-testid={`grocery-done-${item.id}`}
                  >
                    <Checkbox
                      checked={true}
                      onCheckedChange={() => handleToggle(item)}
                      className="border-sage data-[state=checked]:bg-sage"
                    />
                    <span className="flex-1 text-navy-light line-through">{item.name}</span>
                    {item.quantity !== '1' && (
                      <span className="text-sm text-navy-light/50">{item.quantity}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default GroceryPage;
