import React from "react";
import {
  Brush,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { ClusterPoint } from "../../types";

interface Props {
  data: ClusterPoint[];
}

const COLORS = ["#ef4444", "#06b6d4", "#f59e0b"];
const CLUSTER_NAMES: { [key: number]: string } = {
  1: "Low Generation / Night",
  2: "Moderate / Transition",
  0: "High Output / Peak",
};

export const PredictionClusterVisuals: React.FC<Props> = ({ data }) => {
  // Defensive check: ensure data is an array
  const safeData = Array.isArray(data) ? data : [];

  if (safeData.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center text-slate-500">
        No prediction cluster data available
      </div>
    );
  }

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <XAxis
            type="number"
            dataKey="x"
            name="Time"
            stroke="#64748b"
            tick={{ fontSize: 10 }}
            tickFormatter={(unixTime) => new Date(unixTime).getHours() + "h"}
            label={{
              value: "Time of Day",
              position: "bottom",
              offset: 0,
              fill: "#64748b",
              fontSize: 12,
            }}
            domain={["auto", "auto"]}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Predicted Solar MW"
            stroke="#64748b"
            tick={{ fontSize: 10 }}
            label={{
              value: "Predicted Solar (MW)",
              angle: -90,
              position: "insideLeft",
              fill: "#64748b",
              fontSize: 12,
            }}
          />
          <ZAxis type="number" range={[50, 50]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload;
                const clusterId = point.cluster_id;
                const clusterName =
                  CLUSTER_NAMES[clusterId] || `Cluster ${clusterId}`;

                return (
                  <div className="bg-slate-800 border border-slate-700 p-2 rounded text-xs text-white shadow-lg">
                    <p className="font-semibold mb-1 text-cyan-400">
                      {clusterName}
                    </p>
                    <p>Time: {new Date(point.x).toLocaleString()}</p>
                    <p>Predicted: {point.y.toFixed(2)} MW</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter name="Prediction Clusters" data={safeData} fill="#8884d8">
            {safeData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[(entry.cluster_id || 0) % COLORS.length]}
              />
            ))}
          </Scatter>
          <Brush
            data={safeData}
            dataKey="x"
            height={30}
            stroke="#94a3b8"
            fill="#1e293b"
            tickFormatter={(unixTime) => new Date(unixTime).getHours() + "h"}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};
