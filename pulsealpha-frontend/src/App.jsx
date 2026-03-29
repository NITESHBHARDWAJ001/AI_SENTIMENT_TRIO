import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { AuthLayout } from "./layouts/AuthLayout";
import { DashboardLayout } from "./layouts/DashboardLayout";
import { PublicLayout } from "./layouts/PublicLayout";
import { LoginPage } from "./pages/auth/LoginPage";
import { SignupPage } from "./pages/auth/SignupPage";
import { AlertsPage } from "./pages/dashboard/AlertsPage";
import { DashboardHomePage } from "./pages/dashboard/DashboardHomePage";
import { PortfolioPage } from "./pages/dashboard/PortfolioPage";
import { SavedNewsPage } from "./pages/dashboard/SavedNewsPage";
import { SettingsPage } from "./pages/dashboard/SettingsPage";
import { WatchlistPage } from "./pages/dashboard/WatchlistPage";
import { AboutPage } from "./pages/public/AboutPage";
import { CompanyDetailPage } from "./pages/public/CompanyDetailPage";
import { HomePage } from "./pages/public/HomePage";
import { MarketOverviewPage } from "./pages/public/MarketOverviewPage";
import { NewsFeedPage } from "./pages/public/NewsFeedPage";
import { PredictionsPage } from "./pages/public/PredictionsPage";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/market" element={<MarketOverviewPage />} />
            <Route path="/company/:ticker" element={<CompanyDetailPage />} />
            <Route path="/predictions" element={<PredictionsPage />} />
            <Route path="/news" element={<NewsFeedPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Route>

          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
          </Route>

          <Route path="/app" element={<DashboardLayout />}>
            <Route index element={<DashboardHomePage />} />
            <Route path="watchlist" element={<WatchlistPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="saved-news" element={<SavedNewsPage />} />
            <Route path="portfolio" element={<PortfolioPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
