"use client";

import { useEffect, useState } from "react";
import { fetchAnalytics, type DataStatus } from "@/lib/analytics-data";
import type { AnalyticsDataMap, AnalyticsKey } from "@/lib/types";

export function useAnalytics<K extends AnalyticsKey>(key: K): DataStatus<AnalyticsDataMap[K]> {
  const [state, setState] = useState<DataStatus<AnalyticsDataMap[K]>>({
    status: "loading",
    data: null,
    error: null,
  });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading", data: null, error: null });
    fetchAnalytics(key, controller.signal)
      .then((data) => setState({ status: "success", data, error: null }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          data: null,
          error: error instanceof Error ? error.message : "An unexpected data error occurred.",
        });
      });
    return () => controller.abort();
  }, [key]);

  return state;
}
