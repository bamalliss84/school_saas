import { useMemo } from 'react';
import { useToast } from '../context';

/** The toast context value changes on every toast; expose only its stable callbacks for effect deps. */
export const useStableToast = () => {
  const { success, error } = useToast();
  return useMemo(() => ({ success, error }), [success, error]);
};
