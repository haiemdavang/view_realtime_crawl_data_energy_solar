import React, { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Brush } from 'recharts';
import { Prediction } from '../../types';

interface Props {
  data: Prediction[];
}

export const PredictionChart: React.FC<Props> = ({ data }) => {
  const safeData = useMemo(() => Array.isArray(data) ? data : [], [data]);

  const formatDate = (str: string) => {
    if (!str) return '';
    const date = new Date(str);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleTimeString([], { hour: '2-digit' });
  };

  if (safeData.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center text-slate-500 bg-slate-900/50 rounded-lg">
        No forecast data available
      </div>
    );
  }

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={safeData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorSolar" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatDate}
            stroke="#64748b"
            tick={{ fontSize: 12 }}
            minTickGap={30}
          />
          <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
            itemStyle={{ color: '#f59e0b' }}
            labelFormatter={(label) => label ? new Date(label).toLocaleString() : ''}
          />
          <Area
            type="monotone"
            dataKey="prediction"
            stroke="#f59e0b"
            fillOpacity={1}
            fill="url(#colorSolar)"
            name="Solar Forecast (MW)"
          />
          <Brush dataKey="timestamp" height={30} stroke="#94a3b8" fill="#1e293b" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};