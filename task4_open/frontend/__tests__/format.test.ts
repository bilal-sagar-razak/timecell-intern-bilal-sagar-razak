import { describe, expect, test } from "vitest"
import { formatINR, formatPct } from "@/lib/format"

describe("formatINR", () => {
  test("formats 10000000 as Indian grouping", () => {
    expect(formatINR(10000000)).toBe("1,00,00,000")
  })
  test("formats 80000 with thousand separator", () => {
    expect(formatINR(80000)).toBe("80,000")
  })
  test("formats small numbers without separators", () => {
    expect(formatINR(500)).toBe("500")
  })
  test("formats negative numbers with sign prefix", () => {
    expect(formatINR(-12345)).toBe("-12,345")
  })
  test("formats 0", () => {
    expect(formatINR(0)).toBe("0")
  })
})

describe("formatPct", () => {
  test("default no sign for positive", () => {
    expect(formatPct(8.0)).toBe("8.00%")
  })
  test("withSign adds + for positive", () => {
    expect(formatPct(8.0, true)).toBe("+8.00%")
  })
  test("negative always has - regardless of withSign", () => {
    expect(formatPct(-3.21, true)).toBe("-3.21%")
  })
})
