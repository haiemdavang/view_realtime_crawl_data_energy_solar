import {
  Activity,
  AlertCircle,
  Calendar,
  RefreshCw,
  Sun,
  TrendingUp,
  Wind,
  Zap,
} from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { StatCard } from "../components/StatCard";
import { ClusterVisuals } from "../components/charts/ClusterVisuals";
import { CorrelationMatrix } from "../components/charts/CorrelationMatrix";
import {
  MainTimeSeriesChart,
  SeasonalChart,
  TrendChart,
} from "../components/charts/MainTimeSeriesChart";
import { PowerHistogram } from "../components/charts/PowerHistogram";
import { PredictionChart } from "../components/charts/PredictionChart";
import { PredictionClusterVisuals } from "../components/charts/PredictionClusterVisuals";
import { GridService } from "../services/api";
import {
  ClusterPoint,
  CorrelationData,
  GridStatus,
  Measurement,
  Prediction,
  SeasonalData,
  TimeRange,
  TrendData,
} from "../types";

export const Dashboard: React.FC = () => {
  // State
  const [timeRange, setTimeRange] = useState<TimeRange>("day");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [clusteringLoading, setClusteringLoading] = useState<boolean>(false);
  const [analysisLoading, setAnalysisLoading] = useState<boolean>(false);
  const [predictionLoading, setPredictionLoading] = useState<boolean>(false);

  // Data
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [status, setStatus] = useState<GridStatus | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [correlations, setCorrelations] = useState<CorrelationData>({});
  const [clusters, setClusters] = useState<ClusterPoint[]>([]);
  const [predictionClusters, setPredictionClusters] = useState<ClusterPoint[]>(
    []
  );
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [seasonalData, setSeasonalData] = useState<SeasonalData[]>([]);

  // Fetch all data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        measData,
        statusData,
        predData,
        corrData,
        clusterData,
        predClusterData,
        trendRes,
        seasonalRes,
      ] = await Promise.all([
        GridService.getMeasurements(timeRange),
        GridService.getLatestStatus(),
        GridService.getPredictions(),
        GridService.getCorrelations(),
        GridService.getClustering(timeRange),
        GridService.getClusteringPrediction(),
        GridService.getTrendAnalysis(timeRange),
        GridService.getSeasonalAnalysis(timeRange),
      ]);

      setMeasurements(measData);
      setStatus(statusData);
      setPredictions(predData);
      setCorrelations(corrData);
      setClusters(clusterData);
      setPredictionClusters(predClusterData);
      setTrendData(trendRes);
      setSeasonalData(seasonalRes);
    } catch (err: any) {
      console.error(err);
      setError(
        "Failed to connect to Grid Backend. Ensure API is running at localhost:8000"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(async () => {
      try {
        const latest = await GridService.getLatestStatus();
        setStatus(latest);
      } catch (e) {
        console.error("Polling failed", e);
      }
    }, 60000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const maxTimestamp = useMemo(() => {
    if (!measurements || measurements.length === 0) return null;

    return measurements.reduce((max, item) => {
      const currentTime = new Date(item.timestamp).getTime();
      return currentTime > max ? currentTime : max;
    }, new Date(measurements[0].timestamp).getTime());
  }, [measurements]);

  useEffect(() => {
    if (!status || !status.timestamp) return;

    const statusTime = new Date(status.timestamp).getTime();

    if (statusTime < maxTimestamp || measurements.length === 0) {
      fetchData();
    }
  }, [maxTimestamp, status]);

  const handleManualClustering = async () => {
    setClusteringLoading(true);
    try {
      await GridService.triggerClustering();
      // Refresh all data to show new clusters immediately for both Grid and Prediction
      await fetchData();
    } catch (err) {
      alert("Failed to trigger analysis");
    } finally {
      setClusteringLoading(false);
    }
  };

  const handleTriggerDataAnalysis = async () => {
    setAnalysisLoading(true);
    try {
      await GridService.triggerDataAnalysis();
      await fetchData();
    } catch (err) {
      alert("Failed to trigger data analysis");
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleTriggerPrediction = async () => {
    setPredictionLoading(true);
    try {
      await GridService.triggerPrediction();
      await fetchData();
    } catch (err) {
      alert("Failed to trigger prediction");
    } finally {
      setPredictionLoading(false);
    }
  };

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-10">
        <AlertCircle size={48} className="text-red-500 mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">System Offline</h2>
        <p className="text-slate-400 mb-6">{error}</p>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-primary hover:bg-cyan-600 text-white rounded-lg transition-colors"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Los Angeles Grid Status
          </h1>
          <p className="text-slate-400 text-sm">
            Real-time monitoring and predictive analytics
          </p>
        </div>

        <div className="flex items-center gap-3 bg-surface p-1 rounded-lg border border-slate-800">
          {(["day", "week", "month"] as TimeRange[]).map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md capitalize transition-all ${
                timeRange === r
                  ? "bg-slate-700 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {r}
            </button>
          ))}
          <div className="w-px h-6 bg-slate-700 mx-1" />
          <button
            onClick={handleManualClustering}
            disabled={clusteringLoading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw
              size={14}
              className={clusteringLoading ? "animate-spin" : ""}
            />
            <span>
              {clusteringLoading ? "Clustering..." : "Trigger Clustering"}
            </span>
          </button>
          <button
            onClick={handleTriggerDataAnalysis}
            disabled={analysisLoading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <Activity
              size={14}
              className={analysisLoading ? "animate-spin" : ""}
            />
            <span>
              {analysisLoading ? "Analyzing..." : "Trigger Data Analysis"}
            </span>
          </button>
          <button
            onClick={handleTriggerPrediction}
            disabled={predictionLoading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <TrendingUp
              size={14}
              className={predictionLoading ? "animate-spin" : ""}
            />
            <span>
              {predictionLoading ? "Predicting..." : "Trigger Prediction"}
            </span>
          </button>
        </div>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Load"
          value={`${status?.total_power?.toLocaleString() ?? "0"} MW`}
          subValue="Current Demand"
          icon={Activity}
          color="secondary"
        />
        <StatCard
          label="Grid State"
          value={status?.cluster_label || "Unknown"}
          subValue="Classification"
          icon={Zap}
          color="primary"
        />
        <StatCard
          label="Solar Input"
          value={`${
            measurements.length > 0
              ? measurements[measurements.length - 1]?.solar?.toFixed(1)
              : "0"
          } MW`}
          subValue="Real-time Production"
          icon={Sun}
          color="accent"
        />
        <StatCard
          label="Prediction Cluster"
          // Sử dụng cluster_label đã được xử lý từ API
          value={
            predictions.length > 0 ? predictions[0].cluster_label : "Pending"
          }
          subValue="Latest Analysis"
          icon={TrendingUp}
          color="secondary"
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time Series - Takes up 2 columns */}
        <div className="lg:col-span-2 bg-surface border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Activity size={18} className="text-primary" />
              Power Generation Sources
            </h3>
            <span className="text-xs text-slate-500 bg-slate-900 px-2 py-1 rounded">
              Live Data
            </span>
          </div>
          {loading ? (
            <div className="h-[400px] flex items-center justify-center">
              Loading...
            </div>
          ) : (
            <MainTimeSeriesChart data={measurements} />
          )}
        </div>

        {/* Predictions - Takes up 1 column */}
        <div className="bg-surface border border-slate-800 rounded-xl p-6 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <TrendingUp size={18} className="text-accent" />
              Solar Forecast (24h)
            </h3>
          </div>
          <div className="flex-1">
            {loading ? (
              <div className="h-[300px]">Loading...</div>
            ) : (
              <PredictionChart data={predictions} />
            )}
          </div>
          <div className="mt-4 p-3 bg-slate-900/50 rounded-lg border border-slate-800">
            <p className="text-xs text-slate-400">
              Predictions based on historical weather patterns and current
              atmospheric conditions.
            </p>
          </div>
        </div>
      </div>

      {/* Trend & Seasonality Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-surface border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-blue-500" />
            Load Trend Analysis
          </h3>
          <TrendChart data={trendData} />
        </div>
        <div className="bg-surface border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Calendar size={18} className="text-emerald-500" />
            Daily Seasonality Profile
          </h3>
          <SeasonalChart data={seasonalData} />
        </div>
      </div>

      {/* Analysis Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Correlation Matrix */}
        <div className="bg-surface border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <RefreshCw size={18} className="text-emerald-500" />
            Source Correlation
          </h3>
          <CorrelationMatrix data={correlations} />
        </div>

        {/* Load Distribution */}
        <div className="bg-surface border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Wind size={18} className="text-secondary" />
            Load Distribution
          </h3>
          <PowerHistogram data={measurements} />
        </div>

        {/* Clustering */}
        <div className="bg-surface border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Calendar size={18} className="text-primary" />
            State Clustering
          </h3>
          <ClusterVisuals data={clusters} />
        </div>

        {/* Prediction Clustering */}
        <div className="bg-surface border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-secondary" />
            Prediction Clustering
          </h3>
          <PredictionClusterVisuals data={predictionClusters} />
        </div>
      </div>
    </div>
  );
};
