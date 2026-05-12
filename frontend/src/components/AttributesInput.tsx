import { useMemo } from 'react';

export type AttributePair = { key: string; value: string };

type Props = {
  value: AttributePair[];
  onChange: (next: AttributePair[]) => void;
};

function parsePairs(pairs: AttributePair[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const p of pairs) {
    const k = p.key.trim();
    if (k) {
      out[k] = p.value;
    }
  }
  return out;
}

export function useAttributesObject(pairs: AttributePair[]): Record<string, string> {
  return useMemo(() => parsePairs(pairs), [pairs]);
}

export function AttributesInput({ value, onChange }: Props) {
  const rows = value.length ? value : [{ key: '', value: '' }];

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">Attributes (optional)</span>
        <button
          type="button"
          className="text-xs font-medium text-slate-600 hover:text-slate-900"
          onClick={() => onChange([...rows, { key: '', value: '' }])}
        >
          Add row
        </button>
      </div>
      {rows.map((row, i) => (
        <div key={i} className="flex gap-2">
          <input
            placeholder="Key"
            className="w-1/3 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            value={row.key}
            onChange={(e) => {
              const next = rows.slice();
              next[i] = { ...row, key: e.target.value };
              onChange(next);
            }}
          />
          <input
            placeholder="Value"
            className="flex-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            value={row.value}
            onChange={(e) => {
              const next = rows.slice();
              next[i] = { ...row, value: e.target.value };
              onChange(next);
            }}
          />
        </div>
      ))}
    </div>
  );
}
