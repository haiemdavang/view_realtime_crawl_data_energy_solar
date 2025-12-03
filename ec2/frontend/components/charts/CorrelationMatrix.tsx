import React from 'react';
import { CorrelationData } from '../../types';

interface Props {
  data: CorrelationData;
}

export const CorrelationMatrix: React.FC<Props> = ({ data }) => {
  if (!data || Object.keys(data).length === 0) return <div className="text-slate-500">No correlation data</div>;

  const keys = Object.keys(data);

  const formatLabel = (key: string) => key.replace('_mw', '').charAt(0).toUpperCase() + key.replace('_mw', '').slice(1);

  // Helper to determine color intensity based on correlation value (-1 to 1)
  const getColor = (value: number) => {
    const absVal = Math.abs(value);
    if (value > 0) {
      // Positive correlation: Cyan
      return `rgba(6, 182, 212, ${absVal})`; // cyan-500
    } else {
      // Negative correlation: Rose
      return `rgba(244, 63, 94, ${absVal})`; // rose-500
    }
  };

  return (
    <div className="w-full overflow-x-auto">
      <div className="inline-block min-w-full">
        <div className="grid" style={{ gridTemplateColumns: `auto repeat(${keys.length}, minmax(60px, 1fr))` }}>
          {/* Header Row */}
          <div className="h-10"></div> {/* Empty corner */}
          {keys.map((key) => (
            <div key={key} className="h-10 flex items-center justify-center font-medium text-xs text-slate-400 capitalize">
              {formatLabel(key)}
            </div>
          ))}

          {/* Rows */}
          {keys.map((rowKey) => (
            <React.Fragment key={rowKey}>
              {/* Row Label */}
              <div className="h-12 flex items-center justify-end pr-4 font-medium text-xs text-slate-400 capitalize">
                {formatLabel(rowKey)}
              </div>
              {/* Cells */}
              {keys.map((colKey) => {
                const value = data[rowKey]?.[colKey];

                if (value === undefined || value === null) {
                  return (
                    <div
                      key={`${rowKey}-${colKey}`}
                      className="h-12 m-0.5 rounded flex items-center justify-center text-xs font-bold text-slate-600 bg-slate-900"
                    >
                      -
                    </div>
                  );
                }

                return (
                  <div
                    key={`${rowKey}-${colKey}`}
                    className="h-12 m-0.5 rounded flex items-center justify-center text-xs font-bold text-white transition-all hover:scale-105"
                    style={{ backgroundColor: getColor(value) }}
                    title={`${rowKey} vs ${colKey}: ${value.toFixed(2)}`}
                  >
                    {value.toFixed(2)}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};