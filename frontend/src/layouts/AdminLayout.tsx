import { Outlet, Link, useLocation } from "react-router-dom";
import { Shield, Users, Key, FileText, Database, Settings } from "lucide-react";

export default function AdminLayout() {
  const location = useLocation();

  const navItems = [
    { path: "/admin", label: "Dashboard", icon: Shield },
    { path: "/admin/users", label: "Users", icon: Users },
    { path: "/admin/roles", label: "Roles", icon: Key },
    { path: "/admin/audit-logs", label: "Audit Logs", icon: FileText },
    { path: "/admin/models", label: "Models", icon: Database },
    { path: "/admin/settings", label: "Settings", icon: Settings },
  ];

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-muted/30">
        <div className="flex h-full flex-col">
          <div className="flex h-14 items-center border-b px-4">
            <Shield className="h-6 w-6 text-primary" />
            <span className="ml-2 font-semibold">Admin Panel</span>
          </div>

          <nav className="flex-1 space-y-1 p-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center rounded-md px-3 py-2 text-sm font-medium ${
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
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <header className="border-b px-6 py-4">
          <h1 className="text-2xl font-bold">Administration</h1>
        </header>
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
