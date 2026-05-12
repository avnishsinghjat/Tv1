import { NavLink, Outlet } from 'react-router-dom';

import { getStoredUsername, logout } from '../api/auth';

export function Layout() {
  const username = getStoredUsername();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-baseline gap-6">
            <span className="text-lg font-semibold text-slate-900">Teamcenter Analytics</span>
            <nav className="flex gap-4 text-sm">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  isActive ? 'font-medium text-slate-900' : 'text-slate-600 hover:text-slate-900'
                }
              >
                Workbench
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            {username ? <span>{username}</span> : null}
            <button
              type="button"
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-slate-700 shadow-sm hover:bg-slate-50"
              onClick={() => {
                logout();
                window.location.href = '/login';
              }}
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
