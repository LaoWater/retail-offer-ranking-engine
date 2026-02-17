import { CATEGORY_DISPLAY } from '../../types/metro';

interface Props {
  categories: string[];
  activeCategory: string | null;
  onSelect: (category: string | null) => void;
}

export default function CategoryTabs({ categories, activeCategory, onSelect }: Props) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
      <button
        className={`shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all ${
          activeCategory === null
            ? 'bg-metro-blue text-white shadow-md'
            : 'bg-white text-metro-gray-700 border border-metro-gray-200 hover:border-metro-blue-light hover:text-metro-blue'
        }`}
        onClick={() => onSelect(null)}
      >
        Toate
      </button>

      {categories.map((cat) => (
        <button
          key={cat}
          className={`shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all ${
            activeCategory === cat
              ? 'bg-metro-blue text-white shadow-md'
              : 'bg-white text-metro-gray-700 border border-metro-gray-200 hover:border-metro-blue-light hover:text-metro-blue'
          }`}
          onClick={() => onSelect(cat)}
        >
          {CATEGORY_DISPLAY[cat] || cat}
        </button>
      ))}
    </div>
  );
}
