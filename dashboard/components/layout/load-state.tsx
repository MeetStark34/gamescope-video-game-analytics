import { AlertCircle, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";
import type { DataStatus } from "@/lib/analytics-data";

export function PageDataState({ states, children }: {
  states: DataStatus<unknown>[];
  children: ReactNode;
}) {
  const failure = states.find((state) => state.status === "error");
  if (failure?.status === "error") {
    return <div className="state-card error-state" role="alert"><AlertCircle size={19} /><span>{failure.error}</span></div>;
  }
  if (states.some((state) => state.status === "loading")) {
    return <div className="state-card" role="status"><LoaderCircle className="spin" size={19} /> Loading prepared analytics…</div>;
  }
  return children;
}

export function LoadState<T>({ state, children, empty = "No records match this view." }: {
  state: DataStatus<T>;
  children: (data: T) => ReactNode;
  empty?: string;
}) {
  if (state.status === "loading") {
    return <div className="state-card" role="status"><LoaderCircle className="spin" size={19} /> Loading prepared analytics…</div>;
  }
  if (state.status === "error") {
    return <div className="state-card error-state" role="alert"><AlertCircle size={19} /><span>{state.error}</span></div>;
  }
  if (Array.isArray(state.data) && state.data.length === 0) {
    return <div className="state-card"><span>{empty}</span></div>;
  }
  return children(state.data);
}
