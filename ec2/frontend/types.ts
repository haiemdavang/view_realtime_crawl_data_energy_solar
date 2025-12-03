export type TimeRange = 'day' | 'week' | 'month';

export interface Measurement {
  timestamp: string;
  solar: number;
  wind: number;
  gas: number;
  hydro: number;
  load: number;
  cluster_id?: number;
}

export interface GridStatus {
  total_power: number;
  cluster_id: number;
  cluster_label?: string; // Optional friendly label
  timestamp: string;
}

export interface Prediction {
  timestamp: string;
  prediction: number; // Solar MW
  cluster_id?: number;
  cluster_label?: string;
}

export interface CorrelationData {
  [key: string]: {
    [key: string]: number;
  };
}

export interface ClusterPoint {
  x: number;
  y: number;
  cluster_id: number;
  load: number;
}

export interface TrendData {
  timestamp: string;
  avg_load: number;
  avg_solar: number;
  avg_wind: number;
}

export interface SeasonalData {
  hour: number;
  hour_label: string;
  avg_load: number;
  avg_solar: number;
  avg_wind: number;
}

export interface ApiError {
  message: string;
  status?: number;
}
