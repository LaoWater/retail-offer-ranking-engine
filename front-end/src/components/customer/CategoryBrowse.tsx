import { CATEGORY_DISPLAY } from '../../types/metro';

const FOOD_CATEGORIES = [
  'meat_poultry', 'seafood', 'fruits_vegetables', 'dairy_eggs',
  'bakery_pastry', 'beverages_alcoholic', 'beverages_non_alcoholic',
  'confectionery_snacks', 'deli_charcuterie', 'frozen_foods',
  'grocery_staples', 'condiments_spices', 'coffee_tea',
];

const NON_FOOD_CATEGORIES = [
  'cleaning_detergents', 'kitchen_utensils_tableware', 'paper_packaging',
  'personal_care_hygiene', 'household_goods', 'office_supplies',
  'horeca_equipment', 'electronics_small_appliances',
];

const categoryIcons: Record<string, string> = {
  meat_poultry: '🥩', seafood: '🐟', dairy_eggs: '🧀',
  fruits_vegetables: '🥦', beverages_non_alcoholic: '🥤', bakery_pastry: '🥖',
  frozen_foods: '🧊', grocery_staples: '🌾', beverages_alcoholic: '🍷',
  confectionery_snacks: '🍫', deli_charcuterie: '🥓', condiments_spices: '🧂',
  coffee_tea: '☕', cleaning_detergents: '🧹', kitchen_utensils_tableware: '🍳',
  horeca_equipment: '🏨', paper_packaging: '📦', personal_care_hygiene: '🧴',
  household_goods: '🏠', office_supplies: '📎', electronics_small_appliances: '🔌',
};

function CategoryGrid({ title, categories }: { title: string; categories: string[] }) {
  return (
    <div>
      <h3 className="text-lg font-bold text-metro-gray-900 mb-4">{title}</h3>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
        {categories.map((cat) => (
          <div
            key={cat}
            className="bg-white rounded-xl p-4 text-center hover:shadow-md transition-shadow cursor-pointer border border-metro-gray-100"
          >
            <div className="text-3xl mb-2">{categoryIcons[cat] || '📦'}</div>
            <div className="text-xs font-medium text-metro-gray-700">
              {CATEGORY_DISPLAY[cat] || cat}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function CategoryBrowse() {
  return (
    <div className="space-y-8">
      <CategoryGrid title="Produse Alimentare" categories={FOOD_CATEGORIES} />
      <CategoryGrid title="Produse Nealimentare" categories={NON_FOOD_CATEGORIES} />
    </div>
  );
}
