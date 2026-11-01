import type { FeatureCollection, Geometry, Polygon } from "geojson";
import { describe, expect, it } from "vitest";

import { rewindForD3 } from "./geo";

const ccw = [
  [0, 0],
  [1, 0],
  [1, 1],
  [0, 1],
  [0, 0],
];

describe("rewindForD3", () => {
  it("deixa o anel externo no sentido horário e os buracos no anti-horário", () => {
    const hole = [
      [0.2, 0.2],
      [0.2, 0.8],
      [0.8, 0.8],
      [0.2, 0.2],
    ];
    const collection: FeatureCollection<Geometry, null> = {
      type: "FeatureCollection",
      features: [
        { type: "Feature", properties: null, geometry: { type: "Polygon", coordinates: [ccw, hole] } },
      ],
    };
    const [outer, inner] = (rewindForD3(collection).features[0]?.geometry as Polygon).coordinates;
    expect(outer).toEqual([...ccw].reverse());
    expect(inner).toEqual([...hole].reverse());
  });

  it("trata MultiPolygon e mantém pontos", () => {
    const collection: FeatureCollection<Geometry, null> = {
      type: "FeatureCollection",
      features: [
        { type: "Feature", properties: null, geometry: { type: "MultiPolygon", coordinates: [[ccw]] } },
        { type: "Feature", properties: null, geometry: { type: "Point", coordinates: [1, 2] } },
      ],
    };
    const [multi, point] = rewindForD3(collection).features;
    expect(multi?.geometry).toEqual({ type: "MultiPolygon", coordinates: [[[...ccw].reverse()]] });
    expect(point?.geometry).toEqual({ type: "Point", coordinates: [1, 2] });
  });
});
