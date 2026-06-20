# Slugify — requirements

### REQ-001: Lowercase and hyphenate
Convert a title to a URL slug: lowercase, spaces collapsed to single hyphens.
Acceptance: slugify("Hello World") returns "hello-world".

### REQ-002: Reject empty input
A slug cannot be made from nothing.
Acceptance: slugify("") throws an Error rather than returning a value.
