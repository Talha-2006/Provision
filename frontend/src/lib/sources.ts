import "server-only";

import sourceData from "../data/sources.json";

export type Source = {
  id: string;
  title: string;
  url: string;
  jurisdiction: string;
  topic: string;
  source_type: string;
  enabled: boolean;
};

export function getEnabledSources() {
  return (sourceData as Source[]).filter((source) => source.enabled);
}
