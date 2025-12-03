import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Brush } from 'recharts';
import { Measurement, TrendData, SeasonalData } from '../../types';

interface Props {
  data: Measurement[];
}

export const MainTimeSeriesChart: React.FC<Props> = ({ data }) => {
  const safeData = useMemo(() => Array.isArray(data) ? data : [], [data]);

  // Simple formatter for XAxis
  const formatDate = (str: string) => {
    if (!str) return '';
    const date = new Date(str);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (safeData.length === 0) {
    return (
      <div className="w-full h-[400px] flex items-center justify-center text-slate-500 bg-slate-900/50 rounded-lg">
        No measurement data available
      </div>
    );
  }

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={safeData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatDate}
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            minTickGap={30}
          />
          <YAxis
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            label={{ value: 'MW', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
            itemStyle={{ color: '#e2e8f0' }}
            labelFormatter={(label) => label ? new Date(label).toLocaleString() : ''}
          />
          <Legend />
          <Line type="monotone" dataKey="solar" stroke="#f59e0b" strokeWidth={2} dot={false} name="Solar" />
          <Line type="monotone" dataKey="wind" stroke="#06b6d4" strokeWidth={2} dot={false} name="Wind" />
          <Line type="monotone" dataKey="gas" stroke="#ef4444" strokeWidth={2} dot={false} name="Gas" />
          <Line type="monotone" dataKey="hydro" stroke="#3b82f6" strokeWidth={2} dot={false} name="Hydro" />
          <Line type="monotone" dataKey="load" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Total Load" />
          <Brush dataKey="timestamp" height={30} stroke="#94a3b8" fill="#1e293b" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

interface TrendChartProps {
  data: TrendData[];
}

export const TrendChart: React.FC<TrendChartProps> = ({ data }) => {
  const formatDate = (str: string) => {
    if (!str) return '';
    const date = new Date(str);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleDateString();
  };

  if (!data || data.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center text-slate-500 bg-slate-900/50 rounded-lg">
        No data for trend analysis
      </div>
    );
  }

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatDate}
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            minTickGap={40}
          />
          <YAxis
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            label={{ value: 'MW', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
            labelFormatter={(label) => label ? new Date(label).toLocaleString() : ''}
            formatter={(value: number) => [value.toFixed(2), 'MW']}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="avg_load"
            name="Avg Load"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="avg_solar"
            name="Avg Solar"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
          />
          <Brush dataKey="timestamp" height={30} stroke="#94a3b8" fill="#1e293b" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

interface SeasonalChartProps {
  data: SeasonalData[];
}

export const SeasonalChart: React.FC<SeasonalChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center text-slate-500 bg-slate-900/50 rounded-lg">
        No data for seasonal analysis
      </div>
    );
  }

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
          <XAxis
            dataKey="hour_label"
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            interval={2}
          />
          <YAxis
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            label={{ value: 'Avg MW', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
            formatter={(value: number) => [value.toFixed(2), 'Avg MW']}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="avg_load"
            name="Avg Load Profile"
            stroke="#10b981"
            strokeWidth={3}
            dot={{ r: 4, fill: '#10b981', strokeWidth: 0 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="avg_solar"
            name="Avg Solar Profile"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
          />
          <Brush dataKey="hour_label" height={30} stroke="#94a3b8" fill="#1e293b" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};