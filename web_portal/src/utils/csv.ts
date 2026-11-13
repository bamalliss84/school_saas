export type CsvRow = Record<string, string>;

/**
 * Parse RFC 4180 CSV text into header-keyed rows.
 * Handles quoted fields, escaped quotes (""), embedded commas/newlines,
 * CRLF line endings and a leading UTF-8 BOM. Blank lines are skipped.
 */
export const parseCsv = (text: string): CsvRow[] => {
  const source = text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
  const records: string[][] = [];
  let record: string[] = [];
  let field = '';
  let quoted = false;

  for (let i = 0; i < source.length; i += 1) {
    const ch = source[i];
    if (quoted) {
      if (ch === '"') {
        if (source[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          quoted = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ',') {
      record.push(field);
      field = '';
    } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && source[i + 1] === '\n') i += 1;
      record.push(field);
      records.push(record);
      record = [];
      field = '';
    } else {
      field += ch;
    }
  }
  if (field !== '' || record.length) {
    record.push(field);
    records.push(record);
  }

  const nonEmpty = records.filter((r) => r.some((v) => v.trim() !== ''));
  if (nonEmpty.length < 2) return [];
  const header = nonEmpty[0].map((h) => h.trim());
  return nonEmpty.slice(1).map((values) =>
    Object.fromEntries(header.map((key, index) => [key, (values[index] ?? '').trim()])),
  );
};

const escapeField = (value: unknown): string => {
  if (value === null || value === undefined) return '';
  const text = typeof value === 'object' ? JSON.stringify(value) : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};

/** Trigger a browser download of CSV text with a UTF-8 BOM so Excel reads Arabic correctly. */
export const downloadCsv = (filename: string, text: string): void => {
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob(['﻿' + text], { type: 'text/csv;charset=utf-8' }));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
};

/** Serialize rows to RFC 4180 CSV using the given column order. */
export const toCsv = (rows: Record<string, unknown>[], keys: string[]): string =>
  [keys.map(escapeField).join(','), ...rows.map((row) => keys.map((key) => escapeField(row[key])).join(','))].join('\r\n');
