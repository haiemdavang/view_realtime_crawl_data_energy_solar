import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Measurement } from '../../types';

interface Props {
  data: Measurement[];
}

export const PowerHistogram: React.FC<Props> = ({ data }) => {
  const histogramData = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) return [];

    const loads = data.map(d => d.load);
    const min = Math.min(...loads);
    const max = Math.max(...loads);

    // Handle single value or no variance
    if (min === max) {
      return [{ range: `${min}`, count: loads.length }];
    }

    const binCount = 10;
    const binSize = (max - min) / binCount;

    const bins = Array.from({ length: binCount }, (_, i) => ({
      range: `${Math.round(min + i * binSize)}-${Math.round(min + (i + 1) * binSize)}`,
      count: 0
    }));

    loads.forEach(load => {
      const binIndex = Math.min(
        Math.floor((load - min) / binSize),
        binCount - 1
      );
      if (bins[binIndex]) {
        bins[binIndex].count++;
      }
    });

    return bins;
  }, [data]);

  if (histogramData.length === 0) {
    return <div className="w-full h-[250px] flex items-center justify-center text-slate-500">No data</div>;
  }

  return (
    <div className="w-full h-[250px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={histogramData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <XAxis
            dataKey="range"
            stroke="#64748b"
            tick={{ fontSize: 10 }}
            label={{ value: 'Load Range (MW)', position: 'bottom', offset: 0, fill: '#64748b', fontSize: 12 }}
          />
          <YAxis
            stroke="#64748b"
            tick={{ fontSize: 10 }}
            label={{ value: 'Frequency', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 12 }}
          />
          <Tooltip
            cursor={{ fill: '#334155', opacity: 0.2 }}
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
          />
          <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Frequency" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};