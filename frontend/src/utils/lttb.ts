/**
 * Largest-Triangle-Three-Buckets downsampling algorithm.
 * Reduces data points while preserving visual characteristics.
 */
export interface DataPoint {
  x: number;
  y: number;
}

export function lttb(data: DataPoint[], threshold: number): DataPoint[] {
  if (data.length <= threshold) return data;

  const result: DataPoint[] = [];
  result[0] = data[0];
  result[threshold - 1] = data[data.length - 1];

  const bucketSize = (data.length - 2) / (threshold - 2);

  let a = 0;

  for (let i = 1; i < threshold - 1; i++) {
    const avgStart = Math.floor((i) * bucketSize) + 1;
    const avgEnd = Math.min(Math.floor((i + 1) * bucketSize) + 1, data.length);
    let avgX = 0;
    let avgY = 0;
    const avgLen = avgEnd - avgStart;
    for (let j = avgStart; j < avgEnd; j++) {
      avgX += data[j].x;
      avgY += data[j].y;
    }
    avgX /= avgLen;
    avgY /= avgLen;

    const rangeStart = Math.floor((i - 1) * bucketSize) + 1;
    const rangeEnd = Math.min(Math.floor(i * bucketSize) + 1, data.length);

    let maxArea = -1;
    let maxIdx = rangeStart;

    const ax = data[a].x;
    const ay = data[a].y;

    for (let j = rangeStart; j < rangeEnd; j++) {
      const area = Math.abs(
        (ax - avgX) * (data[j].y - ay) - (ax - data[j].x) * (avgY - ay)
      );
      if (area > maxArea) {
        maxArea = area;
        maxIdx = j;
      }
    }

    result[i] = data[maxIdx];
    a = maxIdx;
  }

  return result;
}
