export type Raw = any
export interface Investigation { id: string; stationId: string; status: string; stage: string; lat: number; lon: number; createdAt?: string; durationSec?: number; raw: Raw }
export interface ReviewPayload { reviewer: string; comments: string }
