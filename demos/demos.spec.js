// Verifies that every demo page tells the truth about its recorded trace.
//
// The page is a view over demo.json, which was produced by running the app's
// real Python module. These checks assert the view has not drifted from the
// record: same steps, same order, same verdicts, same denial reasons. A page
// that rendered an outcome the recorded run did not produce fails here.

const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

// Both the primitives and the compositions that exercise them: a composition's
// page has to tell the truth about its recording for the same reason an app's
// does.
const ROOTS = ["apps", "compositions"].map((d) => path.join(__dirname, "..", d));

const demos = ROOTS.filter((dir) => fs.existsSync(dir)).flatMap((dir) =>
  fs
    .readdirSync(dir)
    .filter((name) => fs.existsSync(path.join(dir, name, "demo.json")))
    .map((name) => ({
      name,
      dir: path.join(dir, name),
      trace: JSON.parse(
        fs.readFileSync(path.join(dir, name, "demo.json"), "utf-8")
      ),
    }))
);

test("at least one demo exists to check", () => {
  expect(demos.length).toBeGreaterThan(0);
});

for (const demo of demos) {
  test.describe(demo.name, () => {
    const pageUrl = pathToFileURL(path.join(demo.dir, "demo.html")).href;

    test.beforeEach(async ({ page }) => {
      await page.goto(pageUrl);
    });

    test("states the app name and its atomic claim", async ({ page }) => {
      await expect(page.locator("#app")).toHaveText(demo.name);
      await expect(page.locator("#claim")).toHaveText(demo.trace.claim);
    });

    test("shows one step marker per recorded step", async ({ page }) => {
      await expect(page.locator(".dot")).toHaveCount(demo.trace.steps.length);
    });

    test("every step renders the verdict the real run produced", async ({ page }) => {
      for (let i = 0; i < demo.trace.steps.length; i++) {
        const step = demo.trace.steps[i];
        await expect(page.locator("#stage")).toHaveAttribute("data-step", String(i));

        const verdict = page.locator(".verdict");
        await expect(verdict).toHaveAttribute("data-outcome", step.outcome);
        await expect(verdict.locator(".tag")).toHaveText(
          step.outcome === "allowed" ? "ALLOWED" : "DENIED"
        );

        if (step.outcome === "denied") {
          // The denial reason on screen must be the one the module raised.
          await expect(page.locator(".reason")).toHaveAttribute(
            "data-reason",
            step.reason
          );
        }

        if (i < demo.trace.steps.length - 1) {
          await page.locator("#next").click();
        }
      }
    });

    test("the verdict animates in rather than appearing pre-rendered", async ({ page }) => {
      const name = await page
        .locator(".verdict")
        .evaluate((el) => getComputedStyle(el).animationName);
      expect(name).toBe("stamp");
    });

    test("navigation bounds hold at both ends", async ({ page }) => {
      await expect(page.locator("#prev")).toBeDisabled();
      const last = demo.trace.steps.length - 1;
      for (let i = 0; i < last; i++) await page.locator("#next").click();
      await expect(page.locator("#next")).toBeDisabled();
      await page.locator("#replay").click();
      await expect(page.locator("#stage")).toHaveAttribute("data-step", "0");
    });

    test("makes no network requests", async ({ page }) => {
      const external = [];
      page.on("request", (r) => {
        if (!r.url().startsWith("file://")) external.push(r.url());
      });
      await page.reload();
      await page.locator("#next").click();
      expect(external).toEqual([]);
    });
  });
}
