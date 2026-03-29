import { apiClient } from "./apiClient";
import { getAllPredictions } from "./publicService";

const hasItems = (value) => Array.isArray(value) && value.length > 0;
const hasObject = (value) => Boolean(value) && typeof value === "object";

const emptyPortfolio = {
  holdings: [],
  summary: {
    totalInvested: 0,
    currentValue: 0,
    totalPnl: 0,
    totalPnlPct: 0
  }
};

export async function getDashboardData() {
  try {
    const [{ data: watchlistData }, { data: portfolioData }, predictionRows, alertsRows] = await Promise.all([
      apiClient.get("/api/watchlist"),
      apiClient.get("/api/portfolio"),
      getAllPredictions(),
      getAlerts()
    ]);

    const watchlist = Array.isArray(watchlistData)
      ? watchlistData.map((row) => ({
          ticker: row.ticker,
          price: Number(row.price || 0),
          change: Number(row.change || 0),
          sentiment: row.sentiment || "Neutral",
          hasLatestHourReport: Boolean(row.hasLatestHourReport),
          latestNewsMessage: row.latestNewsMessage || "No recent report status",
        }))
      : [];

    const holdings = hasItems(portfolioData?.holdings) ? portfolioData.holdings : emptyPortfolio.holdings;
    const summary = hasObject(portfolioData?.summary) ? portfolioData.summary : emptyPortfolio.summary;

    const mappedPredictions = Array.isArray(predictionRows) ? predictionRows : [];
    const topPrediction = mappedPredictions.sort((a, b) => Number(b.confidence || 0) - Number(a.confidence || 0))[0];

    return {
      welcomeName: "PulseAlpha User",
      kpis: {
        watchlistSentiment: watchlist.length ? "0.58" : "0.00",
        watchlistPerformance: `${summary.totalPnlPct >= 0 ? "+" : ""}${summary.totalPnlPct.toFixed(2)}%`,
        alertsTriggered: Array.isArray(alertsRows) ? alertsRows.length : 0,
        savedArticles: 0,
        strongestPrediction: topPrediction ? `${topPrediction.ticker} ${Math.round(topPrediction.confidence)}%` : "N/A"
      },
      watchlist: hasItems(watchlist) ? watchlist : [],
      alerts: Array.isArray(alertsRows) ? alertsRows : [],
      predictions: hasItems(mappedPredictions) ? mappedPredictions : [],
      portfolio: {
        holdings,
        summary
      }
    };
  } catch {
    return {
      welcomeName: "PulseAlpha User",
      kpis: {
        watchlistSentiment: "0.00",
        watchlistPerformance: "0.00%",
        alertsTriggered: 0,
        savedArticles: 0,
        strongestPrediction: "N/A"
      },
      watchlist: [],
      alerts: [],
      predictions: [],
      portfolio: emptyPortfolio
    };
  }
}

export async function getAlerts() {
  try {
    const { data } = await apiClient.get("/api/alerts");
    const mapped = Array.isArray(data)
      ? data.map((row) => ({
          id: row.id,
          ticker: row.ticker,
          message: row.message,
          time: row.time || row.created_at || "N/A"
        }))
      : [];

    return hasItems(mapped) ? mapped : [];
  } catch {
    return [];
  }
}

export async function createAlert(payload) {
  const { data } = await apiClient.post("/api/alerts", payload);
  return data;
}

export async function deleteAlert(alertId) {
  const { data } = await apiClient.delete(`/api/alerts/${alertId}`);
  return data;
}

export async function getWatchlistProgress() {
  try {
    const { data } = await apiClient.get("/api/watchlist/progress");
    return hasItems(data) ? data : [];
  } catch {
    return [];
  }
}

export async function upsertWatchlist(payload) {
  const { data } = await apiClient.post("/api/watchlist", payload);
  return data;
}

export async function removeWatchlist(ticker) {
  const { data } = await apiClient.delete(`/api/watchlist/${ticker}`);
  return data;
}

export async function getProfile() {
  try {
    const { data } = await apiClient.get("/api/profile");
    return data;
  } catch {
    return { id: null, name: "", email: "" };
  }
}

export async function updateProfile(payload) {
  const { data } = await apiClient.put("/api/profile", payload);
  return data;
}

export async function getSavedNews() {
  try {
    const { data } = await apiClient.get("/api/news");
    return hasItems(data) ? data : [];
  } catch {
    return [];
  }
}

export async function getPortfolio() {
  try {
    const { data } = await apiClient.get("/api/portfolio");
    if (hasItems(data?.holdings) || hasObject(data?.summary)) {
      return data;
    }
    return emptyPortfolio;
  } catch {
    return emptyPortfolio;
  }
}

export async function upsertPortfolioHolding(payload) {
  const { data } = await apiClient.post("/api/portfolio", payload);
  return data;
}
