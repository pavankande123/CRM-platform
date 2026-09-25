import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { AppShell } from './components/layout/AppShell';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { AuditPage } from './pages/AuditPage';
import { UsersPage } from './pages/UsersPage';
import { TenantPage } from './pages/TenantPage';
import { Loader2 } from 'lucide-react';

type AuthView = 'login' | 'register';
type MainView = 'dashboard' | 'audit' | 'users' | 'tenant';

const MainApp: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [authView, setAuthView] = useState<AuthView>('login');
  const [mainView, setMainView] = useState<MainView>('dashboard');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex flex-col items-center justify-center text-slate-400 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
        <p className="text-sm font-medium tracking-wide">Initializing Enermax Tenant Session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (authView === 'register') {
      return <RegisterPage onSwitchToLogin={() => setAuthView('login')} />;
    }
    return <LoginPage onSwitchToRegister={() => setAuthView('register')} />;
  }

  return (
    <AppShell currentView={mainView} onNavigate={setMainView}>
      {mainView === 'dashboard' && <DashboardPage onNavigate={setMainView} />}
      {mainView === 'audit' && <AuditPage />}
      {mainView === 'users' && <UsersPage />}
      {mainView === 'tenant' && <TenantPage />}
    </AppShell>
  );
};

export function App() {
  return (
    <ErrorBoundary>
      <NotificationProvider>
        <AuthProvider>
          <MainApp />
        </AuthProvider>
      </NotificationProvider>
    </ErrorBoundary>
  );
}

export default App;
