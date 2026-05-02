import { test, expect } from "@playwright/test"
import path from "path"

test("upload a sample statement, see Overview tab render", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByText("Portfolio Intelligence Dashboard")).toBeVisible()

  const samplePath = path.resolve(
    __dirname,
    "../../backend/samples/sample_zerodha.xlsx",
  )
  await page.setInputFiles('input[type="file"]', samplePath)

  await expect(page.locator("nav a", { hasText: "Overview" }).first()).toBeVisible({ timeout: 60_000 })
  await expect(page.getByText("Allocation")).toBeVisible()
  await expect(page.getByText("XIRR by Fund")).toBeVisible()
  await expect(page.getByText("Category Performance")).toBeVisible()
})
