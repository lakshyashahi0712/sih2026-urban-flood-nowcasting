---
name: human-engineering
description: Engineering guidance for writing simple, explicit, maintainable, domain-driven code. Use whenever building or modifying application code for this project. Favors reliable, understandable implementations over clever ones; avoids unnecessary abstractions, boilerplate, speculative features, excessive dependencies, meaningless comments, duplicate utilities, and generic AI-dashboard patterns. Requires every significant architectural choice to have a reason, and validation against real/project data with a clear distinction between prototype assumptions and scientifically meaningful modelling. Not a general style lint — this is the working contract for how the code here is written.
---

# Human Engineering

Write code a human can read, reason about, and change. The project is a hackathon deliverable, so it must be **demonstrable and defensible** — but that means *clarity and honesty*, not a tower of abstractions.

## Core principles

* **Simple, explicit, maintainable.** Favor the plainest thing that works. A future teammate (or the judges, or next-week you) should understand the code from the file itself.
* **Domain-driven, not pattern-driven.** Name things after the domain (a `pipe`, a `catchment`, a `surcharge` event) — not after generic software patterns. If there's no real abstraction to capture, don't invent one.
* **Every significant choice has a reason.** Before adding a layer of indirection, a dependency, or a new module, state the concrete problem it solves. "It's cleaner" is not a reason. "We need to swap the solver behind this interface" is.
* **Reliable and understandable over clever.** One obvious loop beats a clever one-liner. Optimize for reading and correctness, not for looking impressive.
* **Validate against real/project data.** Code that has never been run against actual data (or a faithful, clearly-labeled stand-in) is not done.
* **Be honest about what is prototype.** Distinguish prototype approximations from scientifically meaningful modelling in both code and comments. Do not let a placeholder masquerade as a calibrated result.

## What to avoid

* **Unnecessary abstractions.** No interfaces, base classes, factories, or dependency-injection containers unless two concrete implementations genuinely exist and are actually needed.
* **Boilerplate.** No getters/setters that add nothing, no config plumbing for options nobody changes, no empty handlers.
* **Speculative features.** Build for the problem in front of you. "We might need X later" is a reason to *not* build X now.
* **Excessive dependencies.** A dependency must earn its place. Prefer stdlib and a small, well-justified set of libraries. Reject a library that saves 10 lines but drags in a transitive stack and a lock-in.
* **Meaningless comments.** No comments that restate the code (`# add 1 to count`). Keep comments that capture *why* — a non-obvious decision, a domain fact, a limitation — and let the code say *what*.
* **Duplicate utilities.** One canonical helper, reused. If two places do the same thing, that's a bug-in-waiting, not an opportunity to abstract — extract once.
* **Generic AI-dashboard patterns.** No default styling boilerplate, fake "insights," decorative charts that don't answer a question, or placeholder "AI assistant" widgets unless the problem actually asks for them. Every UI element should trace back to a domain need.

## What to prefer

* **Flat, obvious structure.** Prefer clear linear code and small named functions over deep class hierarchies.
* **Explicit over implicit.** Passing a value as an argument is clearer than hiding it in global/module state. Make data flow visible.
* **Real names.** A `flood_depth_m` column is worth more than a `val` column. Units in names/type hints prevent whole classes of errors.
* **Domain vocabulary in the UI too.** Labels like "Predicted flood depth at this intersection" mean something to a user; "Insight #4" does not.

## Working contract

* For each meaningful feature: state the domain question it answers before writing code.
* After implementing, validate against real/project data (or a clearly-labeled synthetic stand-in), and record the result. If validation is impossible because data is absent, say so explicitly rather than declaring success.
* Mark prototype approximations in code (e.g. `# PROTOTYPE: uniform rainfall — no gauge data available`). A prototype is allowed; a silent prototype is not.
* Do not fabricate datasets, sensors, hydraulic models, or external APIs to make a demo appear real. If an input is missing, surface it.
