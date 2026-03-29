import { AlertTriangle } from "lucide-react";
import { Button } from "../ui/button";

export function ErrorState({ message = "Something went wrong.", onRetry }) {
  return (
    <div className="flex min-h-52 flex-col items-center justify-center rounded-2xl border border-red-400/30 bg-red-500/5 p-8 text-center">
      <AlertTriangle className="mb-3 text-[#EF4444]" />
      <h3 className="text-base font-semibold text-[#F9FAFB]">Data Fetch Error</h3>
      <p className="mt-1 text-sm text-[#94A3B8]">{message}</p>
      {onRetry ? (
        <Button className="mt-4" onClick={onRetry} variant="secondary">
          Retry
        </Button>
      ) : null}
    </div>
  );
}
