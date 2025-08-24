---
description: Create a technical design document for a feature
argument-hint: [feature name]
allowed-tools: Read, Write, Grep, Glob, LS, Bash
---

# Create Design Document

You'll create a comprehensive technical design document for the feature: **$ARGUMENTS**

## Process

### Phase 1: Codebase Analysis

Before writing the design, analyze the existing codebase to understand:

1. **Current Architecture**
   - Map existing system structure and patterns
   - Identify extension points (interfaces, base classes, registries)
   - Document naming conventions and design patterns in use

2. **Integration Opportunities**
   - Find where the feature can plug into existing systems
   - Prefer extending existing components over creating new ones
   - Note specific files and patterns to follow

3. **Removal Opportunities**
   - Identify code that becomes obsolete with the new feature
   - Find duplicate functionality that can be consolidated
   - Look for deprecated patterns that can be replaced
   - Document what can be safely deleted

### Phase 2: Design Document Creation

Get today's date and create `.design/YYYY-MM-DD-$ARGUMENTS/design.md` with this structure:

## Document Structure

```markdown
# Design: [Feature Name]

## Layer 1: Problem & Requirements

### Problem Statement
[Clear description of the problem and why it matters]

### Current State
[How things work today with specific pain points]

### Requirements
#### Functional
- REQ-001: The system SHALL [specific behavior]
- REQ-002: WHEN [condition] THEN [response]

#### Non-Functional
- Performance: [metrics]
- Security: [requirements]
- Usability: [criteria]

### Constraints
[Technical limitations, compatibility needs]

### Success Criteria
[Measurable outcomes]

## Layer 2: Functional Specification

### User Workflows
1. **[Workflow Name]**
   - User action → System response → Outcome

### External Interfaces
[APIs, UIs, integration points with examples]

### Alternatives Considered
| Option | Pros | Cons | Why Not Chosen |
|--------|------|------|----------------|
| A | [benefits] | [drawbacks] | [reasoning] |

## Layer 3: Technical Specification

### Architecture
[Component diagram and data flow]

### Code Change Analysis
| Component | Action | Justification |
|-----------|--------|---------------|
| [name] | Extend | Uses [existing system] at [path] |
| [name] | Create | Required because [reason] |
| [name] | Remove | Obsolete due to [new feature replacing it] |

### Code to Remove
- **[File/Component]** ([path])
  - Why it's obsolete
  - What replaces it
  - Migration path

### Implementation Approach

**IMPORTANT**: Use simple pseudocode for logic illustration. Full code blocks are HIGHLY discouraged in design docs.

#### Components
- **[Component]** ([path/to/file])
  - Current role
  - Planned changes
  - Integration approach
  - Example logic (pseudocode only):
    ```
    if user authenticated:
      fetch user preferences
      apply theme settings
    else:
      use default theme
    ```

#### Data Models
[Schema changes with migration notes - structure only, no full implementations]

#### Security
[Auth, validation, following patterns from [reference]]

### Testing Strategy
- Unit tests: [approach]
- Integration tests: [scenarios]
- E2E tests: [critical paths]

### Rollout Plan
[Phased approach, feature flags, rollback strategy]
```

## Key Principles

1. **Extension First**: Always prefer extending existing systems
2. **Remove When Possible**: Delete obsolete code when adding new features
3. **Evidence-Based**: Support claims with code references
4. **Incremental**: Design for phased delivery
5. **Testable**: Each component should be independently testable
6. **Pseudocode Only**: Use simple pseudocode, avoid full code implementations

## Deliverable

Save the completed design document as `.design/YYYY-MM-DD-$ARGUMENTS/design.md` where YYYY-MM-DD is today's date.

Ask clarifying questions if needed before creating the document.