/** F1L-6 Excel helpers for the admin import/export center. */

export const IMPORT_KINDS = ['students', 'teachers', 'guardians'] as const;
export const OPERATIONAL_KINDS = ['attendance', 'results', 'timetable', 'homework'] as const;

export const DATA_KIND_LABELS: Record<string, string> = {
  students: 'الطلاب',
  teachers: 'المعلمون',
  guardians: 'أولياء الأمور',
  attendance: 'الحضور',
  results: 'النتائج',
  timetable: 'الجدول الدراسي',
  homework: 'الواجبات',
};

export const isImportKind = (kind: string): boolean => (IMPORT_KINDS as readonly string[]).includes(kind);
export const isOperationalKind = (kind: string): boolean => (OPERATIONAL_KINDS as readonly string[]).includes(kind);
export const isXlsxFile = (file: File): boolean => /\.xlsx$/i.test(file.name);

/** Flatten a `{field: [messages]}` error envelope into readable lines. */
export const errorLines = (errors: unknown): string[] => {
  if (!errors || typeof errors !== 'object') return [];
  return Object.values(errors as Record<string, unknown>).flatMap((value) =>
    Array.isArray(value) ? value.map(String) : [String(value)],
  );
};

export const downloadBlob = (filename: string, blob: Blob): void => {
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
};
