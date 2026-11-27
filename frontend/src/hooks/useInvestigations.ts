import { api } from '../services/api'
import { isLive, normalizeInv, toArray } from '../utils/normalize'
import { useApi } from './useApi'
export const useInvestigations = () =>
  useApi(async () => toArray(await api.list()).map(normalizeInv), [], d => d?.some(i => isLive(i.status)) ? 4000 : 0)
