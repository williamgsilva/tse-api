import type { FeatureCollection, Geometry, Position } from "geojson";

/** Área com sinal (fórmula do laço) em graus: positiva = sentido anti-horário. */
function signedArea(ring: Position[]): number {
  let sum = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const [x1 = 0, y1 = 0] = ring[i] ?? [];
    const [x2 = 0, y2 = 0] = ring[i + 1] ?? [];
    sum += x1 * y2 - x2 * y1;
  }
  return sum / 2;
}

function orient(rings: Position[][]): Position[][] {
  // O d3-geo trabalha na esfera: o anel externo precisa estar no sentido horário e os buracos no
  // anti-horário. A RFC 7946 (seguida pelo IBGE) usa o contrário; sem inverter, cada estado vira
  // "o globo inteiro menos o estado".
  return rings.map((ring, i) => {
    const counterClockwise = signedArea(ring) > 0;
    const isOuter = i === 0;
    return isOuter === counterClockwise ? [...ring].reverse() : ring;
  });
}

function rewindGeometry(geometry: Geometry): Geometry {
  switch (geometry.type) {
    case "Polygon":
      return { ...geometry, coordinates: orient(geometry.coordinates) };
    case "MultiPolygon":
      return { ...geometry, coordinates: geometry.coordinates.map(orient) };
    case "GeometryCollection":
      return { ...geometry, geometries: geometry.geometries.map(rewindGeometry) };
    default:
      return geometry;
  }
}

export function rewindForD3<P>(collection: FeatureCollection<Geometry, P>): FeatureCollection<Geometry, P> {
  return {
    ...collection,
    features: collection.features.map((f) =>
      f.geometry ? { ...f, geometry: rewindGeometry(f.geometry) } : f,
    ),
  };
}
