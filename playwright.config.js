// @ts-check
const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./demos",
  reporter: [["list"]],
  use: { browserName: "chromium" },
  // Pages are self-contained files: no server, no network.
  expect: { timeout: 3000 },
});
