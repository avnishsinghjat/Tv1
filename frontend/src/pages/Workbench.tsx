import { useCallback, useEffect, useState } from 'react';

import { getToken } from '../api/auth';
import { ApiError } from '../api/client';
import { createFetchRun, listFetchRuns, listObjects, type FetchRun, type TCObjectRow } from '../api/fetch';
import { AttributesInput, type AttributePair, useAttributesObject } from '../components/AttributesInput';
import { JsonViewer } from '../components/JsonViewer';

export function WorkbenchPage() {
  const token = getToken();
  const [sourceLabel, setSourceLabel] = useState('');
  const [useCache, setUseCache] = useState(true);
  const [attrRows, setAttrRows] = useState<AttributePair[]>([{ key: '', value: '' }]);
  const attrs = useAttributesObject(attrRows);

  const [runs, setRuns] = useState<FetchRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [objects, setObjects] = useState<TCObjectRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadRuns = useCallback(async () => {
    if (!token) {
      return;
    }
    const data = await listFetchRuns(token);
    setRuns(data);
  }, [token]);

  const loadObjects = useCallback(
    async (runId: string | null) => {
      if (!token) {
        return;
      }
      const data = await listObjects(token, runId, 200);
      setObjects(data);
    },
    [token],
  );

  useEffect(() => {
    if (!token) {
      return;
    }
    void loadRuns().catch((err: unknown) => {
      setError(err instanceof ApiError ? err.message : 'Failed to load runs');
    });
  }, [token, loadRuns]);

  useEffect(() => {
    if (!token) {
      return;
    }
    void loadObjects(selectedRunId).catch((err: unknown) => {
      setError(err instanceof ApiError ? err.message : 'Failed to load objects');
    });
  }, [token, selectedRunId, loadObjects]);

  async function onRunFetch() {
    if (!token) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const label =
        [sourceLabel.trim(), Object.keys(attrs).length ? JSON.stringify(attrs) : ''].filter(Boolean).join(' · ') ||
        null;
      await createFetchRun(token, label, useCache);
      await loadRuns();
      setSelectedRunId(null);
      await loadObjects(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Fetch failed');
    } finally {
      setBusy(false);
    }
  }

  const selectedRun = runs.find((r) => r.id === selectedRunId) ?? null;

  return (
    <div className="space-y-8">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-slate-900">New fetch</h2>
        <p className="mt-1 text-sm text-slate-600">
          In mock mode the API returns sample objects. With a live Teamcenter URL configured, it attempts an HTTP load
          instead.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700">
            Source label
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm"
              value={sourceLabel}
              onChange={(e) => setSourceLabel(e.target.value)}
              placeholder="e.g. engineering release"
            />
          </label>
          <label className="flex items-end gap-2 pb-1 text-sm text-slate-700">
            <input type="checkbox" checked={useCache} onChange={(e) => setUseCache(e.target.checked)} />
            Use cache when Redis is available
          </label>
        </div>
        <div className="mt-4">
          <AttributesInput value={attrRows} onChange={setAttrRows} />
        </div>
        {error ? (
          <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>
        ) : null}
        <div className="mt-4">
          <button
            type="button"
            disabled={busy}
            onClick={() => void onRunFetch()}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {busy ? 'Running…' : 'Run fetch'}
          </button>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-base font-semibold text-slate-900">Recent runs</h2>
            <button
              type="button"
              className="text-xs font-medium text-slate-600 hover:text-slate-900"
              onClick={() => void loadRuns()}
            >
              Refresh
            </button>
          </div>
          <ul className="mt-3 max-h-72 space-y-2 overflow-auto text-sm">
            {runs.map((r) => (
              <li key={r.id}>
                <button
                  type="button"
                  onClick={() => setSelectedRunId((cur) => (cur === r.id ? null : r.id))}
                  className={`w-full rounded-md border px-3 py-2 text-left ${
                    selectedRunId === r.id
                      ? 'border-slate-900 bg-slate-900 text-white'
                      : 'border-slate-200 bg-slate-50 text-slate-800 hover:border-slate-300'
                  }`}
                >
                  <div className="flex justify-between gap-2">
                    <span className="font-medium">{r.status}</span>
                    <span className="opacity-80">{new Date(r.created_at).toLocaleString()}</span>
                  </div>
                  <div className="mt-1 text-xs opacity-80">
                    {r.objects_count} objects
                    {r.source_label ? ` · ${r.source_label}` : ''}
                  </div>
                  {r.error_message ? <div className="mt-1 text-xs text-red-200">{r.error_message}</div> : null}
                </button>
              </li>
            ))}
            {runs.length === 0 ? <li className="text-slate-500">No runs yet.</li> : null}
          </ul>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Stored objects</h2>
          <p className="mt-1 text-sm text-slate-600">
            {selectedRun ? `Filtered to run ${selectedRun.id}` : 'Showing the latest objects from all runs.'}
          </p>
          <div className="mt-3 max-h-[28rem] overflow-auto">
            <JsonViewer data={objects} className="max-h-[28rem]" />
          </div>
        </div>
      </section>

      {selectedRun ? (
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Selected run detail</h2>
          <div className="mt-3 max-h-96 overflow-auto">
            <JsonViewer data={selectedRun} />
          </div>
        </section>
      ) : null}
    </div>
  );
}
