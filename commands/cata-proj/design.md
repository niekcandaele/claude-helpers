---
description: Create a technical design document for a feature
argument-hint: [feature name]
allowed-tools: Read, Write, Grep, Glob, LS, Bash, WebSearch
---

# Create Design Document

You'll create a comprehensive technical design document for the feature: **$ARGUMENTS**

## Process

### Phase 0: Research Modern Best Practices

Before analyzing the codebase, research modern approaches and industry standards:

1. **Industry Research**
   - Search for current best practices for this type of feature
   - Review modern frameworks and libraries that solve similar problems
   - Identify established patterns and common approaches
   - Find recent articles, guides, and official documentation (prefer 2023+)
   - **MUST track and save URLs** for every source consulted

2. **Pattern Discovery**
   - Research proven implementation patterns
   - Identify anti-patterns and common pitfalls to avoid
   - Look for case studies of successful implementations
   - Find benchmarks and performance considerations

3. **Technology Landscape**
   - Survey modern tools and libraries available
   - Review what leading companies/projects use for similar features
   - Check for emerging standards or specifications
   - Identify compatibility and integration requirements

4. **Security & Performance**
   - Research security best practices specific to this feature type
   - Find performance optimization techniques
   - Review accessibility standards if UI-related
   - Check for compliance requirements (GDPR, WCAG, etc.)

**Research Output**: Document 3-5 key findings that will inform the design, including:
- Modern patterns to adopt
- Technologies/libraries to consider
- Anti-patterns to avoid
- Industry standards to follow

**Source Citation Requirements**:
- EVERY research finding MUST include a source URL
- Use markdown link format: `[Article/Doc Title](https://url)`
- Include publication date when available
- Prefer: Official documentation > Recent articles (2023+) > Blog posts
- All claims in the design doc must be traceable to sources

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

## Research & Best Practices

### Industry Findings
[Summary of web research on modern approaches to this feature type]

**Key Sources Consulted**:
- [Source Title 1](https://example.com/article) - Publication Date
- [Source Title 2](https://example.com/docs) - Official Documentation
- [Source Title 3](https://example.com/guide) - 2024 Guide

### Recommended Patterns
1. **[Pattern Name]**
   - Source: [Article/Doc Title](https://url)
   - Description and benefits
   - How it applies to this feature
   - Example use cases from the source

2. **[Another Pattern]**
   - Source: [Official Docs](https://url)
   - Why it's recommended
   - Implementation considerations

### Technologies to Consider
- **[Library/Framework]**: [Why it's relevant]
  - Reference: [Official Docs/Article](https://url)
  - Benefits and trade-offs
- **[Tool/Service]**: [Description]
  - Reference: [Source](https://url)

### Anti-Patterns to Avoid
- **[Bad Pattern]**: [Why to avoid]
  - Source: [Article explaining pitfalls](https://url)
  - Common problems and alternatives

### Standards & Compliance
[Relevant industry standards, security requirements, accessibility guidelines]
- [Standard Name]: [Requirement] - [Official Spec](https://url)
- [Security Practice]: [Description] - [OWASP/NIST Guide](https://url)

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

1. **Research-Informed**: Base design on proven patterns and modern best practices - cite all sources with URLs
2. **Extension First**: Always prefer extending existing systems
3. **Remove When Possible**: Delete obsolete code when adding new features
4. **Evidence-Based**: Support ALL claims with code references and research findings - include clickable source URLs
5. **Incremental**: Design for phased delivery
6. **Testable**: Each component should be independently testable
7. **Pseudocode Only**: Use simple pseudocode, avoid full code implementations

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