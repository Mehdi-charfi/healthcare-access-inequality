// Export Google Search Console search-analytics (the "demand" dataset).
//
// Wraps the local GSC client (~/.gsc/gsc.mjs, already OAuth-authorised) and
// dumps tidy CSVs for the last ~16 months — the GSC retention window. Three
// cuts, each a column in the demand story:
//
//   gsc_queries.csv   what patients type        (dim=query)
//   gsc_pages.csv     which SEO pages rank       (dim=page  -> specialty×gouvernorat)
//   gsc_query_page.csv the join key              (dim=query,page)
//
// Run from the project root:  node src/export_gsc.mjs
//
// GSC hides low-volume queries (privacy threshold) and caps history at ~16
// months, so this is a demand *signal*, not a full demand census — state
// that in the writeup.

import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const GSC = "C:/Users/mehdi/.gsc/gsc.mjs";
const SITE = "sc-domain:medline.tn";
const START = "2025-02-10"; // ~16 months back from today
const END = "2026-06-10";
const ROWS = "25000"; // GSC API per-request max

function csvCell(v) {
  const s = v == null ? "" : String(v);
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

// Call the GSC client in --json mode and normalise its rows. The API returns
// `keys` (one per requested dimension) plus the four metrics.
function pull(dims) {
  const out = execFileSync(
    "node",
    [GSC, "query", SITE, "--dim", dims, "--rows", ROWS,
     "--start", START, "--end", END, "--json"],
    { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 },
  );
  const parsed = JSON.parse(out);
  return parsed.rows || [];
}

function dump(dims, file) {
  const dimList = dims.split(",");
  const rows = pull(dims);
  const header = [...dimList, "clicks", "impressions", "ctr", "position"];
  const lines = [header.join(",")];
  for (const r of rows) {
    const cells = [
      ...dimList.map((_, i) => r.keys[i]),
      r.clicks,
      r.impressions,
      r.ctr,
      r.position,
    ];
    lines.push(cells.map(csvCell).join(","));
  }
  writeFileSync(`data/raw/${file}`, lines.join("\n") + "\n");
  console.log(`wrote data/raw/${file}: ${rows.length} rows`);
}

dump("query", "gsc_queries.csv");
dump("page", "gsc_pages.csv");
dump("query,page", "gsc_query_page.csv");
