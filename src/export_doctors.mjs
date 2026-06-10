// Export the medline.tn doctor directory (the "supply" dataset) to CSV.
//
// Source: the medline site's static doctor asset (public/_/x.json) — the
// CNOM national registry, filtered to practising doctors with a usable
// address. Run from the project root:
//
//   node src/export_doctors.mjs
//
// Override the source path with MEDLINE_X_JSON if the site repo lives
// elsewhere. Output -> data/raw/doctors.csv (gitignored: it carries phone
// + email PII, so it never leaves this machine — only derived aggregates
// are committed).

import { readFileSync, writeFileSync } from "node:fs";

const SRC =
  process.env.MEDLINE_X_JSON ||
  "C:/Users/mehdi/Desktop/EX.T.M/medline.tn/medline/medline/public/_/x.json";
const OUT = "data/raw/doctors.csv";

const COLS = [
  "slug",
  "name",
  "firstName",
  "lastName",
  "nameAr",
  "specialtySlug",
  "gouvernoratSlug",
  "delegationGov",
  "delegationSlug",
  "address",
  "phone",
  "email",
  "mapQuery",
];

// RFC-4180 field escaping: wrap in quotes when the value has a comma,
// quote, or newline, and double any embedded quotes.
function csvCell(v) {
  const s = v == null ? "" : String(v);
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

const rows = JSON.parse(readFileSync(SRC, "utf8"));
const lines = [COLS.join(",")];
for (const d of rows) lines.push(COLS.map((c) => csvCell(d[c])).join(","));
writeFileSync(OUT, lines.join("\n") + "\n");

console.log(`wrote ${OUT}: ${rows.length} doctors, ${COLS.length} columns`);
