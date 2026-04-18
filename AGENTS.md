# Kent Beck's Test-Driven Development (TDD)

## Overview

This skill guides software development following Kent Beck's Test-Driven Development methodology, as described in his seminal book "Test-Driven Development: By Example".

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