import { useId, useState } from "react";

import type { Enablement, TimelineBucket } from "../api/types";
import { formatInt } from "../lib/format";

/** Ordem fixa das séries (cor segue a categoria, nunca a posição). */
export const ENABLEMENTS: { key: Enablement; label: string }[] = [
  { key: "biometria", label: "Biometria" },
  { key: "ano_nascimento", label: "Ano de nascimento" },
  { key: "sem_biometria", label: "Sem biometria" },
];

const WIDTH = 720;
const HEIGHT = 240;
const MARGIN = { top: 16, right: 8, bottom: 28, left: 52 };
const GAP = 2;

function niceMax(value: number): number {
  if (value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const step = [1, 2, 2.5, 5, 10].find((s) => s * magnitude >= value / 4) ?? 10;
  return Math.ceil(value / (step * magnitude)) * step * magnitude;
}

/** Retângulo com só os cantos de cima arredondados (a ponta do dado), ancorado na base. */
export function barPath(x: number, y: number, width: number, height: number, radius: number): string {
  const r = Math.max(0, Math.min(radius, width / 2, height));
  return [
    `M${x},${y + height}`,
    `V${y + r}`,
    `Q${x},${y} ${x + r},${y}`,
    `H${x + width - r}`,
    `Q${x + width},${y} ${x + width},${y + r}`,
    `V${y + height}`,
    "Z",
  ].join(" ");
}

function minutes(clock: string): number {
  const [h = "0", m = "0"] = clock.split(":");
  return Number(h) * 60 + Number(m);
}

interface Props {
  buckets: TimelineBucket[];
  /** Linha de referência (HH:MM, horário de Brasília), ex.: o horário de corte "17:00". */
  marker?: string;
  title: string;
}

/** Barras empilhadas de votos por intervalo de horário, por tipo de habilitação do eleitor. */
export function TimelineChart({ buckets, marker, title }: Props) {
  const id = useId();
  const [active, setActive] = useState<number | null>(null);
  if (buckets.length === 0) return null;

  const sorted = buckets.slice().sort((a, b) => minutes(a.inicio) - minutes(b.inicio));
  const first = minutes(sorted[0]?.inicio ?? "00:00");
  const last = minutes(sorted[sorted.length - 1]?.inicio ?? "00:00");
  const step =
    sorted.length > 1
      ? Math.min(...sorted.slice(1).map((b, i) => minutes(b.inicio) - minutes(sorted[i]?.inicio ?? b.inicio)))
      : 15;
  const slots = Math.max(1, (last - first) / step + 1);
  const innerW = WIDTH - MARGIN.left - MARGIN.right;
  const innerH = HEIGHT - MARGIN.top - MARGIN.bottom;
  const slotW = innerW / slots;
  const barW = Math.max(2, slotW - GAP);
  const max = niceMax(Math.max(...sorted.map((b) => b.votos)));
  const y = (value: number) => (value / max) * innerH;
  const x = (clock: string) => MARGIN.left + ((minutes(clock) - first) / step) * slotW;
  const ticks = [0, max / 2, max];
  const hourLabels = sorted.filter((b) => minutes(b.inicio) % 60 === 0);
  const activeBucket = active === null ? null : sorted[active];

  return (
    <figure className="chart" aria-labelledby={`${id}-title`}>
      <figcaption id={`${id}-title`} className="chart__title">
        {title}
      </figcaption>
      <ul className="chart__legend" aria-label="Legenda">
        {ENABLEMENTS.map((e) => (
          <li key={e.key}>
            <span className={`chart__swatch chart__swatch--${e.key}`} aria-hidden="true" />
            {e.label}
          </li>
        ))}
      </ul>
      <div className="chart__plot">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-label={`${title}. Os valores estão na tabela abaixo.`}
        >
          {ticks.map((t) => (
            <g key={t}>
              <line
                className="chart__grid"
                x1={MARGIN.left}
                x2={WIDTH - MARGIN.right}
                y1={MARGIN.top + innerH - y(t)}
                y2={MARGIN.top + innerH - y(t)}
              />
              <text
                className="chart__axis"
                x={MARGIN.left - 6}
                y={MARGIN.top + innerH - y(t) + 4}
                textAnchor="end"
              >
                {formatInt(t)}
              </text>
            </g>
          ))}
          {hourLabels.map((b) => (
            <text
              key={b.inicio}
              className="chart__axis"
              x={x(b.inicio) + barW / 2}
              y={HEIGHT - 8}
              textAnchor="middle"
            >
              {b.inicio.slice(0, 2)}h
            </text>
          ))}
          {sorted.map((bucket, index) => {
            let base = MARGIN.top + innerH;
            const segments = ENABLEMENTS.map((e) => ({
              key: e.key,
              value: bucket.por_habilitacao[e.key] ?? 0,
            })).filter((s) => s.value > 0);
            return (
              <g
                key={bucket.inicio}
                className={`chart__bar${active === index ? " chart__bar--active" : ""}`}
                onMouseEnter={() => setActive(index)}
                onMouseLeave={() => setActive(null)}
              >
                {/* Alvo de hover maior que a barra (coluna inteira). */}
                <rect x={x(bucket.inicio)} y={MARGIN.top} width={slotW} height={innerH} fill="transparent" />
                {segments.map((segment, i) => {
                  const height = Math.max(0, y(segment.value) - (i > 0 ? GAP : 0));
                  base -= y(segment.value);
                  const top = i === segments.length - 1;
                  return (
                    <path
                      key={segment.key}
                      className={`chart__fill chart__fill--${segment.key}`}
                      d={barPath(x(bucket.inicio), base, barW, height, top ? 4 : 0)}
                    />
                  );
                })}
              </g>
            );
          })}
          {marker && minutes(marker) >= first && minutes(marker) <= last + step && (
            <g>
              <line
                className="chart__marker"
                x1={x(marker) - GAP / 2}
                x2={x(marker) - GAP / 2}
                y1={MARGIN.top - 4}
                y2={MARGIN.top + innerH}
              />
              <text className="chart__marker-label" x={x(marker) + 4} y={MARGIN.top + 6}>
                {marker}
              </text>
            </g>
          )}
        </svg>
        {activeBucket && (
          <div className="chart__tooltip" role="status">
            <strong>
              {activeBucket.inicio} · {formatInt(activeBucket.votos)} votos
            </strong>
            {ENABLEMENTS.map((e) => (
              <span key={e.key}>
                <span className={`chart__swatch chart__swatch--${e.key}`} aria-hidden="true" />
                {e.label}: {formatInt(activeBucket.por_habilitacao[e.key] ?? 0)}
              </span>
            ))}
          </div>
        )}
      </div>
      <details className="chart__table">
        <summary>Ver dados em tabela</summary>
        <div className="table-wrap">
          <table className="table table--compact">
            <caption className="visually-hidden">{title}</caption>
            <thead>
              <tr>
                <th scope="col">Início (Brasília)</th>
                <th scope="col" className="num">
                  Total
                </th>
                {ENABLEMENTS.map((e) => (
                  <th key={e.key} scope="col" className="num">
                    {e.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((b) => (
                <tr key={b.inicio}>
                  <td className="mono">{b.inicio}</td>
                  <td className="num">{formatInt(b.votos)}</td>
                  {ENABLEMENTS.map((e) => (
                    <td key={e.key} className="num">
                      {formatInt(b.por_habilitacao[e.key] ?? 0)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}
