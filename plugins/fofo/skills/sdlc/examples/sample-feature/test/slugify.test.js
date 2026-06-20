"use strict";

const { test } = require("node:test");
const assert = require("node:assert");
const { slugify } = require("../src/slugify.js");

test("REQ-001 lowercases and hyphenates a title", () => {
  assert.strictEqual(slugify("Hello World"), "hello-world");
});

// @req: REQ-002
test("rejects empty input", () => {
  assert.throws(() => slugify(""));
});
