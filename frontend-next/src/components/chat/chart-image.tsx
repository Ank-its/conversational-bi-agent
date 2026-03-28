interface ChartImageProps {
  base64: string;
}

export default function ChartImage({ base64 }: ChartImageProps) {
  return (
    <div className="mt-2">
      <img
        src={`data:image/png;base64,${base64}`}
        alt="Chart"
        className="max-w-full rounded border border-zinc-200"
      />
    </div>
  );
}
