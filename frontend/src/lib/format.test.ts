import { describe, expect, it } from "vitest";

import { formatDateTime, formatInt, formatPercent, pad, share, voteKindLabel } from "./format";

describe("format", () => {
  it("formata números no padrão brasileiro", () => {
    expect(formatInt(64256232)).toBe("64.256.232");
    expect(formatInt(null)).toBe("—");
    expect(formatPercent(51.785182884)).toBe("51,79%");
  });

  it("formata datas sem mudar o fuso", () => {
    expect(formatDateTime("2026-10-04T15:40:41")).toBe("04/10/2026 15:40:41");
    expect(formatDateTime("2026-10-04")).toBe("04/10/2026");
    expect(formatDateTime(null)).toBe("—");
  });

  it("utilitários", () => {
    expect(share(1, 4)).toBe(25);
    expect(share(1, 0)).toBe(0);
    expect(pad(77, 4)).toBe("0077");
    expect(voteKindLabel("branco")).toBe("Branco");
    expect(voteKindLabel("outro")).toBe("outro");
  });
});
