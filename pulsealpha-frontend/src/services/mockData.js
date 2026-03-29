export const overviewStats = {
  totalArticles: 28412,
  companiesTracked: 14,
  avgSentiment: 0.63,
  topBullish: "NVDA",
  topBearish: "XOM"
};

export const companies = [
  { ticker: "TSLA", name: "Tesla Inc.", price: 212.32, change: 2.14, sentimentLabel: "Positive" },
  { ticker: "AAPL", name: "Apple Inc.", price: 197.44, change: 0.94, sentimentLabel: "Positive" },
  { ticker: "GOOGL", name: "Alphabet Inc.", price: 162.98, change: 0.52, sentimentLabel: "Neutral" },
  { ticker: "MSFT", name: "Microsoft Corp.", price: 438.62, change: 1.23, sentimentLabel: "Positive" },
  { ticker: "RELIANCE.NS", name: "Reliance Industries", price: 36.45, change: -0.42, sentimentLabel: "Neutral" },
  { ticker: "TCS.NS", name: "Tata Consultancy Services", price: 42.12, change: 0.66, sentimentLabel: "Positive" },
  { ticker: "INFY.NS", name: "Infosys Ltd.", price: 19.48, change: -1.03, sentimentLabel: "Negative" }
];

export const chartSeries = [
  { date: "Mon", price: 182, sentiment: 0.34 },
  { date: "Tue", price: 186, sentiment: 0.41 },
  { date: "Wed", price: 184, sentiment: 0.39 },
  { date: "Thu", price: 191, sentiment: 0.54 },
  { date: "Fri", price: 194, sentiment: 0.61 },
  { date: "Sat", price: 198, sentiment: 0.67 },
  { date: "Sun", price: 202, sentiment: 0.63 }
];

export const latestNews = [
  {
    id: 1,
    title: "AI chip demand lifts tech sentiment across US mega-cap stocks",
    summary: "Analysts report strong enterprise spend signals for AI infrastructure and cloud providers.",
    source: "Reuters",
    publishedAt: "2h ago",
    sentiment: "Positive"
  },
  {
    id: 2,
    title: "Oil volatility drags energy names as macro uncertainty returns",
    summary: "A softer demand outlook weighed on integrated energy stocks during late session.",
    source: "Bloomberg",
    publishedAt: "3h ago",
    sentiment: "Negative"
  },
  {
    id: 3,
    title: "Indian IT exporters gain as deal pipeline improves",
    summary: "Large-cap outsourcing names showed momentum on renewed guidance confidence.",
    source: "Mint",
    publishedAt: "4h ago",
    sentiment: "Positive"
  }
];

export const predictionSnapshot = {
  ticker: "AAPL",
  label: "Moderate Bullish",
  confidence: 78,
  explanation: "Recent positive sentiment and momentum indicate moderate bullish outlook"
};

export const topMovers = [
  { ticker: "NVDA", move: "+4.2%", reason: "Strong AI demand" },
  { ticker: "INFY.NS", move: "-2.1%", reason: "Margin caution" },
  { ticker: "TSLA", move: "+2.6%", reason: "Factory output beat" }
];

export const marketSummary = {
  marketPulse: "Risk-On",
  sectors: [
    { name: "Technology", sentiment: 0.74 },
    { name: "Financials", sentiment: 0.58 },
    { name: "Energy", sentiment: 0.34 },
    { name: "Consumer", sentiment: 0.61 }
  ]
};

export const userDashboard = {
  welcomeName: "Aarav",
  kpis: {
    watchlistSentiment: "0.67",
    watchlistPerformance: "+3.2%",
    alertsTriggered: 5,
    savedArticles: 18,
    strongestPrediction: "MSFT +82%"
  },
  watchlist: [
    { ticker: "MSFT", price: 438.62, change: 1.23, sentiment: "Positive" },
    { ticker: "TSLA", price: 212.32, change: 2.14, sentiment: "Positive" },
    { ticker: "INFY.NS", price: 19.48, change: -1.03, sentiment: "Negative" }
  ],
  alerts: [
    { ticker: "TSLA", time: "09:32", message: "Sentiment crossed +0.70 threshold" },
    { ticker: "INFY.NS", time: "11:12", message: "Price fell below support zone" }
  ]
};

export const modelInfo = {
  sentimentModel: "sentiment_pipeline.pkl",
  predictionModel: "egboost_stock_model.pkl",
  backend: "Flask REST API"
};
