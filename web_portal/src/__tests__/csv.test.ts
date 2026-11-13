import { describe, expect, it } from 'vitest';
import { parseCsv, toCsv } from '../utils/csv';

describe('CSV utilities', () => {
  it('parses quoted fields, escaped quotes, CRLF, BOM and blank lines', () => {
    const text = '﻿full_name,notes,student_code\r\n"Ali, Jr.","said ""hi""",S1\r\n\r\nSara,"line1\nline2",S2\r\n';
    expect(parseCsv(text)).toEqual([
      { full_name: 'Ali, Jr.', notes: 'said "hi"', student_code: 'S1' },
      { full_name: 'Sara', notes: 'line1\nline2', student_code: 'S2' },
    ]);
  });

  it('returns no rows when only a header exists', () => {
    expect(parseCsv('full_name,student_code\n')).toEqual([]);
    expect(parseCsv('')).toEqual([]);
  });

  it('fills missing trailing values with empty strings', () => {
    expect(parseCsv('a,b,c\n1')).toEqual([{ a: '1', b: '', c: '' }]);
  });

  it('round-trips exported rows without adding literal quotes', () => {
    const rows = [
      { full_name: 'Ali, Jr.', note: 'He said "ok"', is_active: true, grade: 5, empty: null },
      { full_name: 'Sara', note: '', is_active: false, grade: 0, empty: undefined },
    ];
    const keys = ['full_name', 'note', 'is_active', 'grade', 'empty'];
    expect(parseCsv(toCsv(rows, keys))).toEqual([
      { full_name: 'Ali, Jr.', note: 'He said "ok"', is_active: 'true', grade: '5', empty: '' },
      { full_name: 'Sara', note: '', is_active: 'false', grade: '0', empty: '' },
    ]);
  });
});
