import { describe, it, expect } from 'vitest';
import { lttb } from '../utils/lttb';
import type { DataPoint } from '../types/api';

describe('lttb', () => {
  it('returns data as-is when below threshold', () => {
    const data: DataPoint[] = [
      { x: 1, y: 2 },
      { x: 2, y: 4 },
      { x: 3, y: 6 },
    ];
    const result = lttb(data, 5);
    expect(result).toEqual(data);
  });

  it('returns exactly threshold number of points', () => {
    const data: DataPoint[] = Array.from({ length: 100 }, (_, i) => ({ x: i, y: Math.sin(i * 0.1) }));
    const result = lttb(data, 20);
    expect(result).toHaveLength(20);
  });

  it('preserves first and last points', () => {
    const data: DataPoint[] = Array.from({ length: 50 }, (_, i) => ({ x: i, y: i * 2 }));
    const result = lttb(data, 10);
    expect(result[0]).toEqual(data[0]);
    expect(result[result.length - 1]).toEqual(data[data.length - 1]);
  });

  it('preserves visual peaks', () => {
    const data: DataPoint[] = [
      { x: 0, y: 0 }, { x: 1, y: 1 }, { x: 2, y: 5 },
      { x: 3, y: 1 }, { x: 4, y: 0 }, { x: 5, y: 1 },
      { x: 6, y: 4 }, { x: 7, y: 1 }, { x: 8, y: 0 },
    ];
    const result = lttb(data, 5);
    const yValues = result.map((p) => p.y);
    expect(yValues).toContain(5);
    expect(yValues).toContain(4);
  });

  it('handles threshold of 2', () => {
    const data: DataPoint[] = [
      { x: 0, y: 0 }, { x: 1, y: 1 }, { x: 2, y: 2 },
    ];
    const result = lttb(data, 2);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual(data[0]);
    expect(result[1]).toEqual(data[data.length - 1]);
  });
});
