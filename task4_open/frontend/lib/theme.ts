/** Color tokens matching globals.css @theme block. Used for chart colors. */
export const colors = {
  bg: "#13110f",
  fg: "#efe8da",
  fgSoft: "#a8a08a",
  rule: "#2a2620",
  ruleSoft: "#1f1c18",
  muted: "#8a8275",
  mutedDeep: "#6a6258",
  mutedDeeper: "#5a5240",
  brass: "#a88b4a",
  brassBright: "#c9a86a",
  oxblood: "#c97a6f",
} as const

/** Donut segment palette — rotates these tones for category slices. */
export const donutPalette = [
  colors.brassBright,
  colors.brass,
  colors.muted,
  colors.mutedDeep,
  colors.mutedDeeper,
  colors.fgSoft,
] as const
