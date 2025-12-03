import axios from 'axios';
import { ClusterPoint, CorrelationData, GridStatus, Measurement, Prediction, SeasonalData, TimeRange, TrendData } from '../types';

const API_BASE_URL = 'http://52.77.236.120:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

const CLUSTER_NAMES: { [key: number]: string } = {
  0: 'Low Generation / Night',   // Thường là nhóm có giá trị thấp nhất
  1: 'Moderate / Transition',    // Nhóm trung bình
  2: 'High Output / Peak',       // Nhóm cao nhất
};

export const GridService = {
  getMeasurements: async (range: TimeRange): Promise<Measurement[]> => {
    const response = await apiClient.get(`/measurements`, {
      params: { range },
    });
    // Backend returns { success: true, data: [...] }
    const rawData = response.data.data || [];

    return rawData.map((item: any) => ({
      timestamp: item.datetime,
      solar: item.solar_mw || 0,
      wind: item.wind_mw || 0,
      gas: item.gas_mw || 0,
      hydro: item.hydro_mw || 0,
      // Calculate total load from available sources
      load: (item.solar_mw || 0) + (item.wind_mw || 0) + (item.gas_mw || 0) +
        (item.hydro_mw || 0) + (item.biomass_mw || 0) +
        (item.geothermal_mw || 0) + (item.unknown_mw || 0),
      cluster_id: item.cluster_id
    }));
  },

  getAnalysis: async (range: TimeRange): Promise<any> => {
    const response = await apiClient.get(`/analysis`, {
      params: { range },
    });
    return response.data.data || [];
  },

  getTrendAnalysis: async (range: TimeRange): Promise<TrendData[]> => {
    const response = await apiClient.get(`/analysis/trend`, {
      params: { range },
    });
    return response.data.data || [];
  },

  getSeasonalAnalysis: async (range: TimeRange): Promise<SeasonalData[]> => {
    const response = await apiClient.get(`/analysis/seasonal`, {
      params: { range },
    });
    return response.data.data || [];
  },

  getCorrelations: async (): Promise<CorrelationData> => {
    const response = await apiClient.get(`/analysis/correlations`);
    return response.data.correlations || {};
  },

  getPredictions: async (): Promise<Prediction[]> => {
    const response = await apiClient.get(`/predictions`);
    const rawData = response.data.data || [];

    return rawData.map((item: any) => {
      const clusterId = item.cluster_id;
      let clusterLabel = 'Pending'; // Trạng thái mặc định cho dự đoán

      if (clusterId !== undefined && clusterId !== null && clusterId !== -1) {
        // Lấy tên từ bảng mapping, nếu không có thì dùng tên dự phòng
        clusterLabel = CLUSTER_NAMES[clusterId] || `Pattern ${clusterId}`;
      }

      return {
        timestamp: item.target_time,
        prediction: item.predicted_solar_mw,
        cluster_id: clusterId,
        cluster_label: clusterLabel // Thêm trường label vào đây
      };
    });
  },

  getLatestStatus: async (): Promise<GridStatus> => {
    const response = await apiClient.get(`/status/latest`);
    const data = response.data;

    // Logic mới: Lấy trực tiếp từ field current_cluster_id backend trả về
    const clusterId = data.current_cluster_id;

    // Tạo label hiển thị có ý nghĩa hơn
    let clusterLabel = 'Unknown';

    if (clusterId !== undefined && clusterId !== null && clusterId !== -1) {
      // Nếu có tên trong bảng mapping thì lấy, không thì hiển thị "Pattern X"
      clusterLabel = CLUSTER_NAMES[clusterId] || `Pattern ${clusterId}`;
    }

    return {
      total_power: data.total_power_mw || 0,
      cluster_id: clusterId ?? -1,
      cluster_label: clusterLabel,
      timestamp: data.latest_measurement?.datetime || data.timestamp || new Date().toISOString()
    };
  },

  getClustering: async (range: TimeRange): Promise<ClusterPoint[]> => {
    const response = await apiClient.get(`/clustering`, {
      params: { range },
    });
    const rawData = response.data.data || [];

    return rawData.map((item: any) => {
      const load = (item.solar_mw || 0) + (item.wind_mw || 0) + (item.gas_mw || 0) +
        (item.hydro_mw || 0) + (item.biomass_mw || 0) +
        (item.geothermal_mw || 0) + (item.unknown_mw || 0);
      return {
        x: item.solar_mw || 0, // Mapping solar to X for visualization
        y: item.wind_mw || 0,  // Mapping wind to Y for visualization
        cluster_id: item.cluster_id,
        load: load
      };
    });
  },

  getClusteringPrediction: async (): Promise<ClusterPoint[]> => {
    const response = await apiClient.get(`/clustering-prediction`);
    const rawData = response.data.data || [];

    return rawData.map((item: any) => {
      return {
        x: new Date(item.target_time).getTime(), // Mapping time to X
        y: item.predicted_solar_mw || 0,         // Mapping predicted solar to Y
        cluster_id: item.cluster_id,
        load: 0 // Not applicable for prediction clustering visualization in this context
      };
    });
  },

  triggerClustering: async (): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/trigger-clustering`);
    return response.data;
  },

  triggerDataAnalysis: async (): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/trigger-analysis`);
    return response.data;
  },

  triggerPrediction: async (): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/trigger-prediction`);
    return response.data;
  },
};