import { expect, test } from "@playwright/test";

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? "http://127.0.0.1:8000";

test.beforeEach(async ({ page, request }) => {
  const response = await request.post(`${API_BASE}/api/login`, {
    data: { username: "user", password: "password" },
  });

  if (!response.ok()) {
    throw new Error(`Login failed with status ${response.status()}`);
  }

  const data = await response.json();
  await page.goto("/");
  await page.evaluate(([token, user]) => {
    localStorage.setItem("kanban-token", token);
    localStorage.setItem("kanban-user", JSON.stringify(user));
  }, [data.access_token, data.user]);
  await page.reload();
});

test("loads the kanban board", async ({ page }) => {
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  const newCard = firstColumn.locator('[data-testid^="card-"]').last();
  await expect(newCard.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  const columns = page.locator('[data-testid^="column-"]');
  await expect(columns).toHaveCount(5);
  const card = page.locator('[data-testid^="card-"]').first();
  await expect(card).toBeVisible();
  const targetColumn = columns.nth(3);
  await expect(targetColumn).toBeVisible();
  const columnBBox = await targetColumn.boundingBox();
  const cardBBox = await card.boundingBox();
  if (!columnBBox || !cardBBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await card.hover();
  await page.mouse.down();
  await page.mouse.move(cardBBox.x + cardBBox.width / 2, cardBBox.y + 50);
  await page.mouse.move(columnBBox.x + columnBBox.width / 2, columnBBox.y + 50);
  await page.mouse.move(columnBBox.x + columnBBox.width / 2, columnBBox.y + 150, {
    steps: 12,
  });
  await page.mouse.up();
  await expect(targetColumn.locator('[data-testid^="card-"]').first()).toBeVisible();
});
