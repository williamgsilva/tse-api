import { formatPercent } from "../lib/format";

/** Barra horizontal com o percentual. O número fica no texto, a barra é só reforço visual. */
export function VoteBar({ percent, highlight = false }: { percent: number; highlight?: boolean }) {
  const width = Math.max(0, Math.min(100, percent));
  return (
    <div className="votebar">
      <div className="votebar__track" aria-hidden="true">
        <div
          className={`votebar__fill${highlight ? " votebar__fill--strong" : ""}`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="votebar__label">{formatPercent(percent)}</span>
    </div>
  );
}
