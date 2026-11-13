type Row = Record<string, unknown>;

export type Conflict = { index?: number; code?: string; message?: string; weekday?: number; period_id?: number };

/** Extract grid-ready conflict objects from a timetable 400 response or a validate result. */
export const timetableConflicts = (value: unknown): Conflict[] => {
  const source = value as Row | undefined;
  const errors = (source as { errors?: unknown })?.errors ?? source;
  if (Array.isArray(errors)) return errors as Conflict[];
  const nested = (errors as Row | undefined)?.conflicts;
  return Array.isArray(nested) ? (nested as Conflict[]) : [];
};
