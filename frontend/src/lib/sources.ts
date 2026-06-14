import "server-only";

import { readFileSync } from "node:fs";
import path from "node:path";

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
  const sourcePath = path.join(process.cwd(), "..", "data", "sources.json");
  const sourceData = JSON.parse(readFileSync(sourcePath, "utf8")) as Source[];

  return sourceData.filter((source) => source.enabled);
}
