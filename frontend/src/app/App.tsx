import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/hooks";
import { useAuthStore } from "@/stores";

// Auth pages
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";

// App pages
import AppLayout from "@/layouts/AppLayout";
import ChatPage from "@/pages/ChatPage";
import AgentsPage from "@/pages/AgentsPage";
import FilesPage from "@/pages/FilesPage";
import SettingsPage from "@/pages/SettingsPage";
import ProfilePage from "@/pages/ProfilePage";

// Admin pages
import AdminLayout from "@/layouts/AdminLayout";
import AdminDashboard from "@/pages/admin/Dashboard";
import AdminUsers from "@/pages/admin/Users";
import AdminRoles from "@/pages/admin/Roles";
import AdminAuditLogs from "@/pages/admin/AuditLogs";
import AdminModels from "@/pages/admin/Models";
import AdminSettings from "@/pages/admin/Settings";

// Protected route component
function ProtectedRoute({ children, adminOnly = false }: { children: React.ReactNode; adminOnly?: boolean }) {
  const { isAuthenticated, isLoading } = useAuth();
  const { isAdmin } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && !isAdmin()) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Access Denied</h1>
          <p className="text-muted-foreground">You do not have permission to access this page.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

// No AI access page
function NoAccessPage() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center p-8">
      <div className="max-w-md text-center">
        <h1 className="mb-4 text-3xl font-bold">Access Pending</h1>
        <p className="mb-6 text-muted-foreground">
          Your account has been created successfully, but AI access has not yet been granted by an administrator.
          Please contact your system administrator to request access.
        </p>
      </div>
    </div>
  );
}

function AppRoutes() {
  const { hasChatAccess } = useAuthStore();

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected app routes */}
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route
          index
          element={hasChatAccess() ? <Navigate to="/app/chat" replace /> : <NoAccessPage />}
        />
        <Route
          path="chat"
          element={hasChatAccess() ? <ChatPage /> : <NoAccessPage />}
        />
        <Route
          path="chat/:conversationId"
          element={hasChatAccess() ? <ChatPage /> : <NoAccessPage />}
        />
        <Route
          path="agents"
          element={hasChatAccess() ? <AgentsPage /> : <NoAccessPage />}
        />
        <Route path="files" element={<FilesPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>

      {/* Protected admin routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute adminOnly>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="users" element={<AdminUsers />} />
        <Route path="roles" element={<AdminRoles />} />
        <Route path="audit-logs" element={<AdminAuditLogs />} />
        <Route path="models" element={<AdminModels />} />
        <Route path="settings" element={<AdminSettings />} />
      </Route>

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  );
}

export default AppRoutes;
