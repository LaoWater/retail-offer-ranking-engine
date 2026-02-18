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

// Inline SVG icons — single-color line style, 24x24 viewBox
function CategoryIcon({ category }: { category: string }) {
  const cls = "w-7 h-7 text-metro-blue";
  const props = { className: cls, fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", strokeWidth: 1.5 };

  switch (category) {
    case 'meat_poultry':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" /><path strokeLinecap="round" strokeLinejoin="round" d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z" /></svg>;
    case 'seafood':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M20.893 13.393l-1.135-1.135a2.252 2.252 0 01-.421-.585l-1.08-2.16a.414.414 0 00-.663-.107.827.827 0 01-.812.21l-1.273-.363a.89.89 0 00-.738.145l-.92.815a1.517 1.517 0 01-1.667.166 3.005 3.005 0 01-.981-.758l-.471-.516a1.266 1.266 0 00-1.713-.13l-.615.492a2.17 2.17 0 00-.462.52L7.2 12.4a.967.967 0 01-.78.468H5.58a2.13 2.13 0 00-1.583.685l-.407.421a.96.96 0 00.09 1.395l.932.753a2.033 2.033 0 002.552.002l.296-.243a1.528 1.528 0 011.717-.127l.758.447a2.043 2.043 0 002.358-.175l.041-.034a1.084 1.084 0 011.516.128l.382.434a2.088 2.088 0 002.557.173l1.17-.855a1.666 1.666 0 00.577-.938l.39-1.584a1.102 1.102 0 01.546-.707z" /></svg>;
    case 'dairy_eggs':
      return <svg {...props}><ellipse cx="12" cy="13" rx="5" ry="6.5" /><path strokeLinecap="round" d="M9 6.5C9 4.5 10.3 3 12 3s3 1.5 3 3.5" /></svg>;
    case 'fruits_vegetables':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 3c-1.2 0-2 .8-2 2v1M9 6C6.2 6 4 9 4 12.5S6.2 20 9 20h6c2.8 0 5-3 5-7.5S17.8 6 15 6H9z" /><path strokeLinecap="round" d="M12 6v7" /></svg>;
    case 'beverages_non_alcoholic':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M8 3h8l-1 18H9L8 3z" /><path strokeLinecap="round" d="M7 8h10" /></svg>;
    case 'bakery_pastry':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-3 0-6 1.5-7 4h14c-1-2.5-4-4-7-4z" /><rect x="4" y="12" width="16" height="4" rx="1" /><path strokeLinecap="round" d="M6 16v2M18 16v2M12 4v2M10 5l-2-1M14 5l2-1" /></svg>;
    case 'frozen_foods':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18M3 12h18M5.636 5.636l12.728 12.728M18.364 5.636L5.636 18.364" /><circle cx="12" cy="12" r="2" /></svg>;
    case 'grocery_staples':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" /></svg>;
    case 'beverages_alcoholic':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M9 20h6M12 16v4M7 4l1.5 7h7L17 4" /><path strokeLinecap="round" d="M8.5 11c0 2 1.6 5 3.5 5s3.5-3 3.5-5" /></svg>;
    case 'confectionery_snacks':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" /></svg>;
    case 'deli_charcuterie':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" /></svg>;
    case 'condiments_spices':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M5 14.5v3.25A2.25 2.25 0 007.25 20h9.5A2.25 2.25 0 0019 17.75V14.5m-14 0h14" /></svg>;
    case 'coffee_tea':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M8 3v2M12 3v2M16 3v2M5 8h14v5a6 6 0 01-6 6h-2a6 6 0 01-6-6V8zM19 10h1a2 2 0 010 4h-1" /></svg>;
    case 'cleaning_detergents':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" /></svg>;
    case 'kitchen_utensils_tableware':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8.25v-1.5m0 1.5c-1.355 0-2.697.056-4.024.166C6.845 8.51 6 9.473 6 10.608v2.513m6-4.87c1.355 0 2.697.055 4.024.165C17.155 8.51 18 9.473 18 10.608v2.513m-3-4.87v-1.5m-6 1.5v-1.5m12 9.75l-1.5.75a3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0L3 16.5m18-4.5a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
    case 'horeca_equipment':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" /></svg>;
    case 'paper_packaging':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" /></svg>;
    case 'personal_care_hygiene':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" /></svg>;
    case 'household_goods':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" /></svg>;
    case 'office_supplies':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" /></svg>;
    case 'electronics_small_appliances':
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" /></svg>;
    default:
      return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" /></svg>;
  }
}

function CategoryGrid({ title, categories }: { title: string; categories: string[] }) {
  return (
    <div>
      <h3 className="text-lg font-bold text-metro-gray-900 mb-4">{title}</h3>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
        {categories.map((cat) => (
          <div
            key={cat}
            className="bg-white rounded-xl p-4 text-center hover-lift cursor-pointer border border-metro-gray-100 group"
          >
            <div className="flex justify-center mb-2 opacity-80 group-hover:opacity-100 transition-opacity">
              <CategoryIcon category={cat} />
            </div>
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
