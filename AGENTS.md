# Kent Beck's Test-Driven Development (TDD)

## Overview

This skill guides software development following Kent Beck's Test-Driven Development methodology, 
as described in his seminal book "Test-Driven Development: By Example".

## Core Principles

### The TDD Cycle: Red-Green-Refactor

1. **Red**: Write a failing test first
   - Write a test that defines a small increment of functionality
   - Run the test and watch it fail (compile errors count as failing)
   - This confirms the test is actually testing something

2. **Green**: Make the test pass
   - Write the minimal amount of code to make the test pass
   - It's okay to write ugly code, hardcode values, or cheat - just get to green
   - Run all tests and confirm they pass

3. **Refactor**: Clean up the code
   - Remove duplication
   - Improve names and structure
   - Keep all tests passing
   - Make small, safe transformations

### The Three Rules of TDD

1. You are not allowed to write any production code unless it is to make a failing unit test pass.
2. You are not allowed to write any more of a unit test than is sufficient to fail; and compilation failures are failures.
3. You are not allowed to write any more production code than is sufficient to pass the one failing unit test.

## Development Guidelines

### Test Writing

- **Start with the simplest test case** - pick the test that teaches you the most with the least effort
- **One concept per test** - each test should verify one piece of behavior
- **Test names should describe behavior** - use descriptive names that explain what should happen
- **Test data should be simple and explicit** - avoid clever test data, make it obvious
- **Tests should be fast, isolated, and repeatable** - no dependencies on external systems

### Incremental Steps

- Take the **smallest possible step** that adds value
- If you're stuck, **make the step even smaller**
- Baby steps are encouraged - TDD is about steady progress, not leaps

### Refactoring Patterns

- **Don't refactor on red** - only refactor when all tests pass
- **Refactor aggressively** - clean code matters, but only after green
- **Common refactorings**:
  - Extract method/function
  - Rename variables and functions for clarity
  - Remove duplication
  - Simplify conditionals

## Working with Fear

Kent Beck describes TDD as a way to manage fear during development:

- Fear leads to tentative, defensive, non-communicative code
- TDD transforms fear into confidence through:
  - Concrete, verifiable progress (tests passing)
  - Clean separation of concerns
  - Confidence to make changes (tests catch regressions)
  - Clear communication through test names

## Testing Patterns

### Fake It ('Til You Make It)
- Return a constant to get the test passing
- Gradually replace constants with variables
- One step at a time

### Triangulation
- Write a test with a specific value
- Write another test with a different value that forces generalization
- Use two examples to force abstraction

### Obvious Implementation
- When the implementation is obvious, just write it
- If you get stuck, return to fake it or triangulation

## Test Structure

Use the **Arrange-Act-Assert** pattern:
- **Arrange**: Set up the test data and context
- **Act**: Execute the code under test
- **Assert**: Verify the expected outcome

## Anti-Patterns to Avoid

- **Writing all tests first** - take it one test at a time
- **Testing implementation details** - test behavior, not structure
- **Skipping the refactor step** - dirty code accumulates technical debt
- **Writing tests after the code** - loses the design benefits of TDD
- **Testing too much at once** - keep tests small and focused

## Good Test F.I.R.S.T
- Fast
- Independent
- Reproducible
- Self-Validating
- Timely

## Confidence Through Tests

The goal of TDD is not just tested code, but:
- **Confidence to change** - tests catch unintended side effects
- **Clean design** - tests force modular, decoupled code
- **Documentation** - tests describe how the code should work
- **Progress tracking** - passing tests show concrete advancement

## George Polya's TDD Heuristic

George Polya taught us to solve problems through four principles. Here is how they guide TDD:

### 1. Understand the Problem
Before writing any test, ask:
- What is the unknown? (The data structure that represents the plot)
- What are the data? (A `Position` with legs, a range of underlying prices)
- What is the condition? (The max-loss point must appear as a black dot; data preparation must be decoupled from rendering)

Can you draw a figure? Sketch the P&L curve at expiration and place the black dot. What does "decoupled" mean? It means the left hand (data preparation) does not know what the right hand (plotting library) is doing. In the future, the right hand might be `matplotlib`, `plotly`, or an interactive web chart. The left hand must not care.

### 2. Devise a Plan
Break the problem into small, verifiable steps. Each test is one step. Ask yourself:
- Have you seen a similar problem? (We already calculate `max_loss()`; now we must locate its coordinates on the curve.)
- Could you solve a part of the problem? (First, just generate the curve points. Then, find the dot. Then, package them. Then, define the adapter contract.)

Your plan should respect the TDD cycle: Red-Green-Refactor. Do not write all tests at once. Write the first, make it pass, clean it, then proceed. If you get stuck, make the step smaller.

### 3. Carry Out the Plan
Write one test. Check your work at each line. Does the test fail for the right reason? Does the minimal code make it pass? Is the refactoring safe? Fear is managed by concrete progress.

### 4. Look Back
After each test, examine the solution. Can you see it at a glance? Is there duplication? Does the design allow for an interactive plot adapter in the future? The separation between data preparation (`PlotDataBuilder`) and rendering (`PlotAdapterPort`) is the key insight that makes scaling possible.

## Challenge: The Black Dot

You must implement a feature that, given a `Position` with legs, prepares data for a P&L curve at expiration and marks the maximum-loss point with a black dot. You must decouple data preparation from actual plotting to allow for future interactive plots.

You have exactly **five tests** to guide your implementation. Follow TDD: write one test, watch it fail, make it pass, refactor, then move to the next. Do not write production code ahead of the tests.

### Test 1 — The Curve Exists
Create a `PlotDataBuilder` (or equivalent name). It takes a `Position` containing one `ShortPut(strike=100, premium=5, volume=1)` and produces P&L curve points for the prices `[0, 50, 100, 150]`. Verify that the returned points match the position's total P&L at each of those prices.

### Test 2 — Find the Darkest Point
Using the same single-leg position and price range, verify that the builder can identify the coordinates of the max-loss point: the price where the worst P&L occurs, paired with that negative P&L value.

### Test 3 — Prepare for the Artist
The builder should return a `PlotData` object (or simple dict) that contains two things: `curve_points` and a `max_loss_marker`. Verify that the marker carries the correct `x`, `y`, and `color="black"`. No plotting library should be imported or invoked in this test.

### Test 4 — The Adapter Contract
Introduce a `PlotAdapterPort` — an abstract interface with a `render(plot_data)` method. Create a `MockPlotAdapter` that implements it and records what it receives. Pass your `PlotData` from Test 3 into `render` and assert that the mock recorded a marker whose `color` is `"black"`.

### Test 5 — Complexity Reveals Truth
Now generalize. Build a two-leg `Position`: `LongPut(strike=100, premium=5, volume=1)` + `ShortPut(strike=90, premium=3, volume=1)`. Use prices `[80, 90, 100, 110]`. Verify that:
1. The curve points are correct.
2. The max-loss marker sits at the correct coordinates (note: the worst loss does **not** occur at price 0 this time).

This last test forces you to handle the general case and confirms that your design is not hard-coded to a single leg or to price=0.

---

*Remember Polya's advice: If you cannot solve the whole problem, solve a part of it. If the step is too big, make it smaller. Good tests are questions you ask your code; listen carefully to the answers.*

## Heuristics that take care of your own brain
### A.2 The 80/24 rule
Write small blocks of code.
In C-based languages like C#, Java, C++, or JavaScript, consider staying within a
80x24 character box. That corresponds to an old terminal window.
Don’t take the threshold values 80 and 24 too literally. I picked them for three reasons:
• They work well in practice
• Continuity with tradition
• Mnemonically, it sounds like the Pareto principle, also known as the 80/20 rule
You can decide on other threshold values. I think the most important part of this rule is
to pick a set of thresholds and consistently stay within those limits.
