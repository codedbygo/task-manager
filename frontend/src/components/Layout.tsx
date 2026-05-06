import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { LayoutDashboard, FolderKanban, LogOut } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 glass-panel m-4 rounded-2xl flex flex-col z-10">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Task Manager</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <Link to="/">
            <Button variant={location.pathname === '/' ? 'secondary' : 'ghost'} className="w-full justify-start">
              <LayoutDashboard className="mr-2 h-4 w-4" />
              Dashboard
            </Button>
          </Link>
          <Link to="/projects">
            <Button variant={location.pathname.startsWith('/projects') ? 'secondary' : 'ghost'} className="w-full justify-start">
              <FolderKanban className="mr-2 h-4 w-4" />
              Projects
            </Button>
          </Link>
        </nav>
        <div className="p-4 border-t">
          <div className="mb-4 px-2">
            <p className="text-sm font-medium">{user?.name}</p>
            <p className="text-xs text-slate-500">{user?.email}</p>
          </div>
          <Button variant="outline" className="w-full justify-start text-destructive" onClick={logout}>
            <LogOut className="mr-2 h-4 w-4" />
            Log out
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto p-8 animate-fade-in z-0">
        <Outlet />
      </main>
    </div>
  );
}
