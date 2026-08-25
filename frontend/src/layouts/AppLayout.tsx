import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks";
import { useAuthStore } from "@/stores";
import {
  MessageSquare,
  Bot,
  FolderOpen,
  Settings,
  User,
  LogOut,
  Shield,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { isAdmin, hasAgentAccess } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navItems = [
    { path: "/app/chat", label: "Chat", icon: MessageSquare },
    { path: "/app/agents", label: "Agents", icon: Bot, requiresPermission: () => hasAgentAccess() },
    { path: "/app/files", label: "Files", icon: FolderOpen },
    { path: "/app/settings", label: "Settings", icon: Settings },
    { path: "/app/profile", label: "Profile", icon: User },
  ];

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const filteredNavItems = navItems.filter((item) => {
    if (item.requiresPermission && !item.requiresPermission()) return false;
    return true;
  });

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-0"
        } flex-shrink-0 border-r bg-muted/30 transition-all duration-300 overflow-hidden`}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-14 items-center border-b px-4">
            <Bot className="h-6 w-6 text-primary" />
            <span className="ml-2 font-semibold">AI Agent Workspace</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            {filteredNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <Icon className="mr-2 h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Admin link */}
          {isAdmin() && (
            <div className="border-t p-4">
              <Link
                to="/admin"
                className="flex items-center rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <Shield className="mr-2 h-4 w-4" />
                Admin Panel
              </Link>
            </div>
          )}

          {/* User info */}
          <div className="border-t p-4">
            <div className="mb-2 text-sm font-medium">{user?.email}</div>
            <Button variant="outline" size="sm" onClick={handleLogout} className="w-full">
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <header className="flex h-14 items-center justify-between border-b px-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </header>
        <div className="p-4">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
