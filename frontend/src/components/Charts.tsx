import { useId, type ChangeEvent } from "react";

import { formatInt, formatPercent, share } from "../lib/format";

export interface BarItem {
  id: string;
  label: string;
  detail?: string | null;
  value: number;
  /** Percentual já calculado (ex.: % dos válidos publicado pelo TSE); senão, a fatia do total. */
  percent?: number | null;
  color: string;
  badge?: string | null;
}

/** Barras horizontais com rótulo e valor diretos (sem eixo): bom para ranking de candidatos. */
export function HBarChart({ items, label, max }: { items: BarItem[]; label: string; max?: number }) {
  const total = items.reduce((sum, item) => sum + item.value, 0);
  const top = max ?? Math.max(1, ...items.map((i) => i.percent ?? share(i.value, total)));
  return (
    <ul className="hbars" aria-label={label}>
      {items.map((item) => {
        const percent = item.percent ?? share(item.value, total);
        return (
          <li key={item.id}>
            <div className="hbar__head">
              <span className="hbar__name">
                {item.label}
                {item.detail && <span className="hbar__party">{item.detail}</span>}
                {item.badge && <span className="badge badge--elected"> {item.badge}</span>}
              </span>
              <span className="hbar__value">
                {formatInt(item.value)}
                <strong>{formatPercent(percent)}</strong>
              </span>
            </div>
            <div className="hbar__track" aria-hidden="true">
              <div
                className="hbar__fill"
                style={{ width: `${Math.max(0.5, (percent / top) * 100)}%`, background: item.color }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export interface CompositionPart {
  id: string;
  label: string;
  value: number;
  color: string;
}

/** Barra 100% (partes de um todo), com legenda que traz valor e percentual. */
export function Composition({ parts, label }: { parts: CompositionPart[]; label: string }) {
  const total = parts.reduce((sum, p) => sum + p.value, 0);
  if (total <= 0) return null;
  return (
    <figure className="chart" aria-label={label}>
      <div className="composition__bar" aria-hidden="true">
        {parts
          .filter((p) => p.value > 0)
          .map((p) => (
            <span key={p.id} style={{ width: `${share(p.value, total)}%`, background: p.color }} />
          ))}
      </div>
      <ul className="chart__legend" style={{ marginTop: 8 }}>
        {parts.map((p) => (
          <li key={p.id}>
            <span className="chart__swatch" style={{ background: p.color }} aria-hidden="true" />
            {p.label}: <strong>{formatInt(p.value)}</strong> ({formatPercent(share(p.value, total))})
          </li>
        ))}
      </ul>
    </figure>
  );
}

interface SegmentedProps<T extends string | number> {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
  hideLabel?: boolean;
}

/** Grupo de botões de opção com visual de controle segmentado (acessível como radio group). */
export function Segmented<T extends string | number>({
  label,
  value,
  options,
  onChange,
  hideLabel,
}: SegmentedProps<T>) {
  const name = useId();
  return (
    <fieldset className="field" style={{ border: 0, padding: 0, margin: 0 }}>
      <legend className={hideLabel ? "visually-hidden" : "field__label"} style={{ marginBottom: 4 }}>
        {label}
      </legend>
      <div className="segmented">
        {options.map((option) => (
          <label key={String(option.value)}>
            <input
              type="radio"
              name={name}
              value={String(option.value)}
              checked={option.value === value}
              onChange={(event: ChangeEvent<HTMLInputElement>) => {
                if (event.target.checked) onChange(option.value);
              }}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
