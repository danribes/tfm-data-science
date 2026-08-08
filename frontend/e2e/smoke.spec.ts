import { expect, test } from "@playwright/test";

test("smoke: boot → lever → persona → persistence → theme → no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (msg) => { if (msg.type() === "error") errors.push(msg.text()); });
  page.on("pageerror", (err) => errors.push(String(err)));

  // boot
  await page.goto("/");
  await expect(page.getByText("España en escenarios").first()).toBeVisible();
  await expect(page.getByText(/proyección condicional, no recomendación/i)).toBeVisible();
  // Scoped to the KPI tile: "223,8" also appears in the debt-vs-GDP reading
  // line ("la ratio pasa de 106,3 a 223,8 %PIB"), which is a strict-mode match.
  await expect(page.locator(".o-val").getByText("223,8")).toBeVisible(); // deuda 2050 at base

  // persona 01: capture gauge figure and chart path
  // (the name matches both the nav pill and Inicio's card link — either navigates)
  await page.getByRole("link", { name: /Bonista/ }).first().click();
  await expect(page.getByText("💼 Inversor en bonos: ¿me pagarán los 10 años?")).toBeVisible();
  // "106,3" appears in the Deuda tile AND the semaphore row — .first() avoids strict-mode
  await expect(page.getByText("106,3").first()).toBeVisible(); // b 2026 base
  const pathBefore = await page.locator("path.recharts-curve").last().getAttribute("d");

  // move the r lever to 4.8 (the S1 vector)
  await page.locator('input[type="range"]').first().fill("4.8");
  await expect(page.getByText("4,80 %")).toBeVisible();
  await expect(page).toHaveURL(/r=4\.8/);
  await expect(page.getByText("107,1").first()).toBeVisible(); // b 2026 moves 106,3 → 107,1
  await expect
    .poll(async () => page.locator("path.recharts-curve").last().getAttribute("d"))
    .not.toBe(pathBefore); // chart path changed
  await expect(page.getByText("S1 tipos +200 pb")).toHaveClass(/on/); // vector now equals S1

  // switch persona: scenario persists (v16 core argument)
  await page.getByRole("link", { name: /Político/ }).click();
  await expect(page.getByText("🗳️ ¿Qué palanca puedo mover sin cruzar una línea roja?")).toBeVisible();
  await expect(page.getByText("4,80 %")).toBeVisible();
  await expect(page.getByText(/🔮 condicional/).first()).toBeVisible();

  // theme toggle persists to <html data-theme>
  await page.getByRole("button", { name: /cambiar tema/i }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  expect(errors).toEqual([]);
});
