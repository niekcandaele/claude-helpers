---
description: Ingest feedback and update design document
argument-hint: [feature name or feedback file path]
allowed-tools: Read, Write, Edit, MultiEdit, Grep, Glob, LS, Bash
---

# Process Design Feedback

Ingest human feedback and update the design document for: **$ARGUMENTS**

## Process

### Step 1: Locate Feedback File

Find the feedback.md file:
- If given a path, use that directly
- If given a feature name, search `docs/design/*/feedback.md`
- Use the most recent feedback file for that feature

### Step 2: Parse Feedback

Read the feedback.md file and extract:
- Original questions/concerns
- Human responses (text after "**Human Response:**")
- Identify which sections of the design need updates

### Step 3: Update Design Document

Based on the feedback, update the design.md file:

1. **Clarify Requirements**
   - Add specificity where ambiguity was identified
   - Update functional/non-functional requirements
   - Refine success criteria

2. **Refine Technical Decisions**
   - Update architecture based on chosen approaches
   - Modify implementation details per feedback
   - Adjust component specifications

3. **Address Concerns**
   - Add mitigation strategies for identified risks
   - Update security/performance considerations
   - Revise integration approaches

4. **Document Decisions**
   - Add "Decision Record" sections where major choices were made
   - Include rationale from human feedback
   - Update alternatives considered

### Step 4: Clean Up

After successfully updating the design:
1. Delete the feedback.md file
2. Report summary of changes made
3. Confirm design is ready for task generation

## Update Guidelines

### When Updating Design:
- Preserve the three-layer structure
- Maintain consistency across all sections
- Add clarifications without removing context
- Mark significant changes with comments if helpful

### Common Updates:
- **Requirements**: Add specific acceptance criteria
- **Interfaces**: Clarify data formats and protocols
- **Architecture**: Specify component boundaries
- **Implementation**: Add technical constraints
- **Testing**: Define specific test scenarios
- **Rollout**: Clarify deployment steps

### Decision Documentation:
When feedback resolves a major decision, add:
```markdown
> **Decision**: [What was decided]
> **Rationale**: [Why this approach based on feedback]
> **Alternative**: [What was not chosen and why]
```

## Example Flow

```
Input: "user-auth"

1. Found feedback at: docs/design/2024-01-15-user-auth/feedback.md

2. Processing 3 feedback items:
   ✓ Question 1: Authentication method
     → Updated to use OAuth 2.0 as specified
   ✓ Question 2: Session duration
     → Set to 24 hours with refresh tokens
   ✓ Concern 3: Database performance
     → Added caching layer specification

3. Design document updated with:
   - OAuth 2.0 integration details
   - Session management specifications
   - Caching architecture

4. Feedback file deleted.

Design ready for task generation!
Next step: Run `/cata-proj/tasks user-auth`
```

## Important Notes

- Ensure all human responses are addressed
- Don't delete feedback until all updates are complete
- Maintain design document quality and completeness
- Suggest next steps (usually task generation)