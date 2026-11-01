import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BRAZIL } from "../test/fixtures";
import { GeoMap } from "./GeoMap";

describe("GeoMap", () => {
  it("desenha áreas focáveis, com tooltip e seleção por clique ou teclado", () => {
    const onSelect = vi.fn();
    render(
      <GeoMap
        geojson={BRAZIL}
        areaId={(f) => String(f.properties.uf)}
        areaLabel={(id) => `Estado ${id}`}
        fill={(id) => (id === "sp" ? "red" : "blue")}
        tooltip={(id) => <strong>Tooltip {id}</strong>}
        onSelect={onSelect}
        selected="ac"
        title="Brasil"
      />,
    );
    const sp = screen.getByRole("button", { name: "Estado sp" });
    expect(sp).toHaveStyle({ fill: "red" });
    expect(sp.getAttribute("d")).toMatch(/^M/);
    expect(screen.getByRole("button", { name: "Estado ac" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.mouseMove(sp, { clientX: 10, clientY: 10 });
    expect(screen.getByRole("status")).toHaveTextContent("Tooltip sp");
    fireEvent.mouseLeave(sp);
    expect(screen.queryByRole("status")).toBeNull();

    fireEvent.click(sp);
    fireEvent.keyDown(screen.getByRole("button", { name: "Estado ac" }), { key: "Enter" });
    expect(onSelect.mock.calls).toEqual([["sp"], ["ac"]]);
  });

  it("esmaece as áreas fora do foco", () => {
    render(
      <GeoMap
        geojson={BRAZIL}
        areaId={(f) => String(f.properties.uf)}
        areaLabel={(id) => id}
        fill={() => "gray"}
        onSelect={() => undefined}
        focus={["ac"]}
        zoomToFocus
        title="Norte"
      />,
    );
    expect(screen.getByRole("button", { name: "sp" })).toHaveClass("map__area--dimmed");
    expect(screen.getByRole("button", { name: "sp" })).toHaveAttribute("tabindex", "-1");
  });
});
