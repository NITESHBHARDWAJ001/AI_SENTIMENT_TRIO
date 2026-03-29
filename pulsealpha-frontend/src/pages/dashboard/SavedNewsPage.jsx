import { useEffect, useState } from "react";
import { NewsCard } from "../../components/common/NewsCard";
import { getSavedNews } from "../../services/userService";

export function SavedNewsPage() {
  const [news, setNews] = useState([]);

  useEffect(() => {
    getSavedNews().then(setNews);
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Saved News</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {news.map((item) => (
          <NewsCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}
