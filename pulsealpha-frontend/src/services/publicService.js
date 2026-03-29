import { apiClient } from "./apiClient";

const hasItems = (value) => Array.isArray(value) && value.length > 0;
const hasObject = (value) => Boolean(value) && typeof value === "object";

const emptyOverview = {
  overviewStats: {
    totalArticles: 0,
    companiesTracked: 0,
    avgSentiment: "0.00",
    topBullish: "N/A",
    topBearish: "N/A"
  },
  companies: [],
  chartSeries: [],
  latestNews: [],
  predictionSnapshot: null,
  topMovers: []
};

export async function getOverview() {
  try {
    const { data } = await apiClient.get("/api/overview");
    if (!hasObject(data)) {
      return emptyOverview;
    }

    return {
      overviewStats: hasObject(data.overviewStats) ? data.overviewStats : emptyOverview.overviewStats,
      companies: hasItems(data.companies) ? data.companies : [],
      chartSeries: hasItems(data.chartSeries) ? data.chartSeries : [],
      latestNews: hasItems(data.latestNews) ? data.latestNews : [],
      predictionSnapshot: hasObject(data.predictionSnapshot) ? data.predictionSnapshot : null,
      topMovers: hasItems(data.topMovers) ? data.topMovers : []
    };
  } catch {
    return emptyOverview;
  }
}

export async function getMarketSummary() {
  try {
    const { data } = await apiClient.get("/api/market-summary");
    if (!hasObject(data)) {
      return { sectors: [], indices: [] };
    }
    return {
      sectors: hasItems(data.sectors) ? data.sectors : [],
      indices: hasItems(data.indices) ? data.indices : []
    };
  } catch {
    return { sectors: [], indices: [] };
  }
}

export async function getCompanyDetail(ticker) {
  try {
    const [companyRes, newsRes, sentimentRes, predictionRes] = await Promise.allSettled([
      apiClient.get(`/api/company/${ticker}`),
      apiClient.get(`/api/company/${ticker}/news`),
      apiClient.get(`/api/company/${ticker}/sentiment`),
      apiClient.get(`/api/company/${ticker}/prediction`)
    ]);

    const companyData = companyRes.status === "fulfilled" ? companyRes.value.data : null;
    const newsData = newsRes.status === "fulfilled" ? newsRes.value.data : [];
    const sentimentData = sentimentRes.status === "fulfilled" ? sentimentRes.value.data : [];
    const predictionData = predictionRes.status === "fulfilled" ? predictionRes.value.data : null;

    return {
      company: hasObject(companyData) ? companyData : null,
      news: hasItems(newsData) ? newsData : [],
      sentimentSeries: hasItems(sentimentData) ? sentimentData : [],
      prediction: hasObject(predictionData) ? predictionData : null
    };
  } catch {
    return { company: null, news: [], sentimentSeries: [], prediction: null };
  }
}

export async function getNewsFeed() {
  try {
    const { data } = await apiClient.get("/api/news");
    return hasItems(data) ? data : [];
  } catch {
    return [];
  }
}

export async function getAllPredictions() {
  try {
    const { data } = await apiClient.get("/api/predictions/all");
    return hasItems(data) ? data : [];
  } catch {
    return [];
  }
}

export async function getModelInfo() {
  try {
    const { data } = await apiClient.get("/api/model-info");
    return hasObject(data) ? data : { modelLoaded: false, modelSource: "backend-unavailable" };
  } catch {
    return { modelLoaded: false, modelSource: "backend-unavailable" };
  }
}

export async function predictManual(payload) {
  try {
    const { data } = await apiClient.post("/api/predict/manual", payload);
    return data;
  } catch (error) {
    throw new Error(error?.response?.data?.error || "Unable to run manual prediction");
  }
}

export async function predictRange(payload) {
  try {
    const { data } = await apiClient.post("/api/predict/range", payload);
    return data;
  } catch (error) {
    throw new Error(error?.response?.data?.error || "Unable to fetch range predictions");
  }
}

export async function searchStocks(params = {}) {
  try {
    const { data } = await apiClient.get("/api/stocks/search", { params });
    return hasObject(data)
      ? {
          count: Number(data.count || 0),
          results: hasItems(data.results) ? data.results : []
        }
      : { count: 0, results: [] };
  } catch {
    return { count: 0, results: [] };
  }
}

export async function ingestNews(payload) {
  const { data } = await apiClient.post("/api/news/ingest", payload);
  return data;
}

export async function getTechnicalIndicators(ticker) {
  try {
    if (!ticker) {
      throw new Error("Ticker is required");
    }
    const { data } = await apiClient.get(`/api/technical/${ticker.toUpperCase()}`);
    return hasObject(data) ? data : null;
  } catch (error) {
    throw new Error(error?.response?.data?.error || "Unable to fetch technical indicators");
  }
}

export async function getSupportedTickers() {
  try {
    const { data } = await apiClient.get("/api/technical/supported");
    return hasObject(data) ? {
      tickers: hasItems(data.tickers) ? data.tickers : [],
      count: Number(data.count || 0)
    } : { tickers: [], count: 0 };
  } catch {
    return { tickers: [], count: 0 };
  }
}
