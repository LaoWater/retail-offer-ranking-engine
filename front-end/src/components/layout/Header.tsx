import { Link, useLocation } from 'react-router-dom';

export default function Header() {
  const location = useLocation();
  const isAdmin = location.pathname === '/admin';

  return (
    <header className="sticky top-0 z-50 bg-metro-blue text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 no-underline">
          <div className="flex items-center">
            <div className="bg-metro-yellow text-metro-blue font-black text-xl px-2 py-0.5 rounded">
              METRO
            </div>
          </div>
          <span className="text-white/80 text-sm hidden sm:block">Romania</span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-1">
          <Link
            to="/"
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline ${
              !isAdmin
                ? 'bg-white/15 text-white'
                : 'text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            Produsele Noastre
          </Link>
          <Link
            to="/admin"
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline ${
              isAdmin
                ? 'bg-white/15 text-white'
                : 'text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            Admin ML
          </Link>
        </nav>

        {/* Store indicator */}
        <div className="hidden md:flex items-center gap-2 text-sm text-white/70">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          METRO Cluj
        </div>
      </div>
    </header>
  );
}
