import { geoMercator, geoPath } from "d3-geo";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { useMemo, useState, type KeyboardEvent, type MouseEvent, type ReactNode } from "react";

import { rewindForD3 } from "../lib/geo";

export type MapFeature = Feature<Geometry, Record<string, unknown>>;

interface Props {
  geojson: FeatureCollection<Geometry, Record<string, unknown>>;
  /** Identificador de cada área (ex.: sigla da UF ou código IBGE do município). */
  areaId: (feature: MapFeature) => string;
  areaLabel: (id: string) => string;
  fill: (id: string) => string;
  tooltip?: (id: string) => ReactNode;
  onSelect?: (id: string) => void;
  selected?: string | null;
  /** Áreas destacadas (as demais ficam esmaecidas); vazio = nenhuma esmaecida. */
  focus?: string[];
  /** Enquadra o mapa só nas áreas em foco (zoom na região). */
  zoomToFocus?: boolean;
  title: string;
  height?: number;
}

const WIDTH = 640;

/** Mapa coroplético em SVG: cada área é focável, clicável e tem tooltip. */
export function GeoMap({
  geojson,
  areaId,
  areaLabel,
  fill,
  tooltip,
  onSelect,
  selected,
  focus = [],
  zoomToFocus = false,
  title,
  height = 520,
}: Props) {
  const [hover, setHover] = useState<{ id: string; x: number; y: number } | null>(null);
  // Chave textual: o array chega novo a cada render e não deve forçar nova projeção.
  const focusKey = focus.join(",");
  const focusSet = useMemo(() => new Set(focusKey ? focusKey.split(",") : []), [focusKey]);

  const oriented = useMemo(() => rewindForD3(geojson), [geojson]);

  const paths = useMemo(() => {
    const framed =
      zoomToFocus && focusSet.size > 0
        ? { ...oriented, features: oriented.features.filter((f) => focusSet.has(areaId(f))) }
        : oriented;
    const projection = geoMercator().fitExtent(
      [
        [8, 8],
        [WIDTH - 8, height - 8],
      ],
      framed,
    );
    const path = geoPath(projection);
    return oriented.features.map((feature) => ({ id: areaId(feature), d: path(feature) ?? "" }));
  }, [oriented, areaId, focusSet, zoomToFocus, height]);

  function move(event: MouseEvent<SVGPathElement>, id: string) {
    const box = event.currentTarget.ownerSVGElement?.parentElement?.getBoundingClientRect();
    if (box) setHover({ id, x: event.clientX - box.left, y: event.clientY - box.top });
  }

  function key(event: KeyboardEvent<SVGPathElement>, id: string) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect?.(id);
    }
  }

  return (
    <div className="map">
      <svg viewBox={`0 0 ${WIDTH} ${height}`} role="group" aria-label={title}>
        {paths.map(({ id, d }) => {
          const dimmed = focusSet.size > 0 && !focusSet.has(id);
          const classes = ["map__area"];
          if (dimmed) classes.push("map__area--dimmed");
          if (selected === id) classes.push("map__area--selected");
          return (
            <path
              key={id}
              d={d}
              className={classes.join(" ")}
              style={{ fill: fill(id) }}
              tabIndex={onSelect && !dimmed ? 0 : -1}
              role={onSelect ? "button" : undefined}
              aria-label={areaLabel(id)}
              aria-pressed={onSelect ? selected === id : undefined}
              onClick={() => onSelect?.(id)}
              onKeyDown={(event) => key(event, id)}
              onMouseMove={(event) => move(event, id)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(null)}
            />
          );
        })}
        {/* A área selecionada é redesenhada por cima para a borda não ficar escondida pelas vizinhas. */}
        {selected &&
          paths
            .filter((p) => p.id === selected)
            .map((p) => (
              <path
                key={`${p.id}-outline`}
                d={p.d}
                className="map__area map__area--selected"
                style={{ fill: "none", pointerEvents: "none" }}
              />
            ))}
      </svg>
      {hover && tooltip && (
        <div className="map__tooltip" style={{ left: hover.x, top: hover.y }} role="status">
          {tooltip(hover.id)}
        </div>
      )}
    </div>
  );
}
