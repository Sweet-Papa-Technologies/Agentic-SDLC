"use strict";

function slugify(input) {
  if (typeof input !== "string" || input.length === 0) {
    throw new Error("input must be a non-empty string");
  }
  return input.trim().toLowerCase().replace(/\s+/g, "-");
}

module.exports = { slugify };
