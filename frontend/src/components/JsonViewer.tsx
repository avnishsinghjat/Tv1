type Props = {
  data: unknown;
  className?: string;
};

export function JsonViewer({ data, className = '' }: Props) {
  const text = JSON.stringify(data, null, 2);
  return (
    <pre
      className={`overflow-auto rounded-md border border-slate-200 bg-slate-950 p-3 text-xs leading-relaxed text-slate-100 ${className}`}
    >
      {text}
    </pre>
  );
}
