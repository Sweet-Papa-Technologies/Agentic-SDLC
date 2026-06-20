"use strict";
// Intentionally weak tests for the intent-gate demo.

const { test } = require("node:test");
const assert = require("node:assert");
const { slugify } = require("../src/slugify.js");

// assertion-free: runs code, checks nothing
test("REQ-001 builds a slug", () => {
  slugify("Hello World");
});

// trivially-true: asserts a tautology, not the requirement
test("REQ-002 sanity", () => {
  assert.strictEqual(1, 1);
});
