/**
 * Determines whether a given sidebar target route is active based on the current pathname.
 * Handles exact matching and subroute prefix matching (e.g. /students/123 matches /students).
 */
export const isRouteActive = (currentPathname: string, targetPath: string): boolean => {
  const normalizedTarget = targetPath.split('?')[0].split('#')[0];
  const normalizedCurrent = currentPathname.split('?')[0].split('#')[0];

  // Exact match
  if (normalizedCurrent === normalizedTarget) {
    return true;
  }

  // Nested subroute match (e.g. /students/123 matches /students, but not /students-other)
  if (
    normalizedTarget !== '/' &&
    normalizedTarget !== '' &&
    normalizedCurrent.startsWith(`${normalizedTarget}/`)
  ) {
    return true;
  }

  return false;
};
