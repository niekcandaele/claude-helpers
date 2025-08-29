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

## Deliverables

1. Save the completed design document as `.design/YYYY-MM-DD-$ARGUMENTS/design.md` where YYYY-MM-DD is today's date.

2. Generate a feedback file at `.design/YYYY-MM-DD-$ARGUMENTS/feedback.md` containing:
   - Questions about ambiguous requirements
   - Concerns about potential implementation issues
   - Requests for clarification on design decisions
   - Areas where multiple approaches exist and guidance is needed

### Feedback File Format

```markdown
# Design Feedback: [Feature Name]

*Please review the questions below and add your responses inline under "**Human Response:**". Your feedback will be used to refine the design document.*

## Questions & Clarifications

### 1. [Topic/Component Name]
**Question**: [Specific question about the design or requirement]
**Context**: [Why this clarification is important for implementation]
**Human Response**: 

### 2. [Another Topic]
**Concern**: [Potential issue or risk identified]
**Impact**: [What could go wrong or be affected]
**Suggested Approach**: [Possible solution if any]
**Human Response**: 

### 3. [Technical Decision]
**Clarification Needed**: [Area needing more specification]
**Options**: 
- Option A: [description]
- Option B: [description]
**Trade-offs**: [Key considerations]
**Human Response**: 
```

Include 3-5 meaningful questions focusing on:
- Ambiguous requirements that could be interpreted multiple ways
- Technical decisions with significant trade-offs
- Integration points that need validation
- Performance or security considerations
- User experience choices

After creating both files, inform the user to:
1. Review and respond to questions in `feedback.md`
2. Run `/cata-proj/feedback [feature-name]` to ingest responses and update the design