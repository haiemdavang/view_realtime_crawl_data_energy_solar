import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'primary' | 'secondary' | 'accent' | 'emerald';
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, subValue, icon: Icon, color = 'primary' }) => {
  const colorClasses = {
    primary: 'text-primary bg-primary/10',
    secondary: 'text-secondary bg-secondary/10',
    accent: 'text-accent bg-accent/10',
    emerald: 'text-emerald-500 bg-emerald-500/10'
  };

  return (
    <div className="bg-surface border border-slate-800 rounded-xl p-6 flex items-start justify-between shadow-lg backdrop-blur-sm">
      <div>
        <p className="text-slate-400 text-sm font-medium mb-1">{label}</p>
        <h3 className="text-2xl font-bold text-white">{value}</h3>
        {subValue && <p className="text-slate-500 text-xs mt-1">{subValue}</p>}
      </div>
      <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
        <Icon size={24} />
      </div>
    </div>
  );
};
