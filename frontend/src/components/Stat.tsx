interface StatProps {
  label: string;
  value: string;
  detail?: string;
}

export function Stat({ label, value, detail }: StatProps) {
  return (
    <div className="stat">
      <dt>{label}</dt>
      <dd>
        <span className="stat__value">{value}</span>
        {detail && <span className="stat__detail">{detail}</span>}
      </dd>
    </div>
  );
}
