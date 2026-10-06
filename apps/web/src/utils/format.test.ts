import { describe, expect, it } from 'vitest';

import { formatPercent } from './format';

describe('formatPercent', () => {
  it('formats manufacturing KPI percentages', () => {
    expect(formatPercent(94.7)).toBe('94.7%');
    expect(formatPercent(87, 0)).toBe('87%');
  });
});
