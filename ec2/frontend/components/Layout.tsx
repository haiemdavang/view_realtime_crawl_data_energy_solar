import React from 'react';
import { Activity, BarChart3, Zap, Settings, Menu } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const SidebarItem = ({ icon: Icon, label, active }: { icon: any, label: string, active?: boolean }) => (
  <div className={`flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-colors ${active ? 'bg-primary/10 text-primary' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}>
    <Icon size={20} />
    <span className="font-medium text-sm">{label}</span>
  </div>
);

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-background text-slate-100 font-sans">
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 w-full z-50 bg-slate-950 border-b border-slate-800 p-4 flex items-center justify-between">
        <span className="font-bold">GridVision</span>
        <Menu size={24} />
      </div>

      {/* Main Content */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto mt-14 md:mt-0">
        <div className="max-w-full mx-auto space-y-8">
          {children}
        </div>
      </main>
    </div>
  );
};
