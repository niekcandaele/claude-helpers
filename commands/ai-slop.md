# AI Slop Detection

## Goal

Identify AI-generated patterns ("slop") in code and text that reveal unnatural, formulaic, or excessively verbose AI writing. This command scans for telltale signs of AI generation to help developers refactor and humanize their codebase.

## Input

Optional scope: $ARGUMENTS (e.g., `docs`, `code`, `comments`, `all`)
- Defaults to checking everything if not specified
- Can specify specific files or directories

## Process

1. **Initial Scan:** Identify file types and prepare analysis scope
2. **Text Pattern Analysis:** Detect formulaic writing in documentation and comments
3. **Code Pattern Detection:** Find AI-generated code signatures
4. **Comment Analysis:** Identify over-commented and unnatural explanations
5. **Structure Analysis:** Detect rigid templating and excessive organization
6. **Generate Slop Report:** Present findings with refactoring recommendations

## Detection Patterns

### 🚨 THE BOLD BULLET EPIDEMIC (Highest Priority AI Tell)

This is the single most obvious AI slop pattern. If your document is full of these, it's almost certainly AI-generated:

#### The Classic AI Bullet Pattern
```markdown
# SCREAMING AI SLOP:
- **Feature Name:** Description of what the feature does
- **Another Thing:** Explanation of this thing  
- **Configuration:** How to configure this item
- **Performance:** Details about performance characteristics
- **Security:** Information about security aspects

# Why this is AI slop:
1. Humans write "Feature X does Y" not "**Feature X:** Does Y"
2. The colon creates unnecessary visual separation
3. It's formulaic and robotic
4. Real documentation flows naturally
```

#### When Bullets Are Actually OK
```markdown
# GOOD - Simple lists without forced structure:
- redis
- postgresql  
- mongodb
- elasticsearch

# GOOD - Action items:
- Fix the login bug
- Update dependencies
- Review PR #234

# BAD - Forced categorization:
- **Redis:** In-memory data store for caching
- **PostgreSQL:** Relational database for persistent storage
- **MongoDB:** Document database for flexible schemas
```

#### The Slop Variations
```markdown
# All of these scream AI:
* **Overview:** This section provides...
1. **Step One:** First, you need to...
- **Note:** It's important to remember...
• **Warning:** Be careful when...
→ **Tip:** You can optimize by...
```

### Text Slop Indicators

#### Formulaic Structure Red Flags
```markdown
# Every Section Follows This Pattern:

## Overview
[Exactly three bullet points with bold prefixes]

## Key Features  
- **Feature Name:** Description that always starts with "Enables"
- **Another Feature:** Description that always starts with "Provides"
- **Third Feature:** Description that always starts with "Allows"

## Benefits
Furthermore, this solution offers...
Moreover, the implementation ensures...
Additionally, users can leverage...
```

#### Overused AI Phrases
- "It's worth noting that..."
- "In essence..."
- "Comprehensive solution"
- "Robust implementation"
- "Elegant approach"
- "Seamless integration"
- "Furthermore," "Moreover," "Additionally" (paragraph starters)
- "Dive deeper," "Delve into," "Explore"
- "Landscape" (as in "the modern development landscape")
- "Leverage" (instead of "use")
- "Utilize" (instead of "use")

#### Excessive Qualifiers
```javascript
// This function may potentially handle user input that could possibly be null
// and might need validation that can ensure proper processing
function processInput(data) {
  // It's worth noting that this validation may help prevent issues
  if (data) {
    // This can potentially process the data
    return data;
  }
}
```

### Code Slop Patterns

#### Over-Commenting Obvious Code
```javascript
// BAD - AI SLOP
// Initialize counter variable to zero
let counter = 0;

// Increment counter by one
counter++;

// Check if counter is greater than 10
if (counter > 10) {
  // Reset counter to zero
  counter = 0;
}

// GOOD - Human
let counter = 0;
counter++;
if (counter > 10) {
  counter = 0;  // Reset after 10 iterations
}
```

#### AI Refactor Traces
```javascript
// processData function (now uses async/await for better performance)
// Updated to handle edge cases (added null checking)
// Refactored for clarity (extracted helper functions)
async function processData(input) {
  // These comments are AI slop - humans don't document like this
}
```

#### Defensive Programming Overload
```javascript
// AI SLOP - Excessive null checking
function calculate(a, b, c) {
  if (a === null || a === undefined) {
    throw new Error('Parameter a cannot be null or undefined');
  }
  if (b === null || b === undefined) {
    throw new Error('Parameter b cannot be null or undefined');
  }
  if (c === null || c === undefined) {
    throw new Error('Parameter c cannot be null or undefined');
  }
  
  try {
    if (typeof a !== 'number') {
      throw new Error('Parameter a must be a number');
    }
    // More defensive checks...
  } catch (error) {
    console.error('An error occurred:', error);
    throw error;
  }
}
```

#### Copy-Paste with Numbered Suffixes
```javascript
// AI SLOP - Lazy naming patterns
function handleUser1() { /* ... */ }
function handleUser2() { /* ... */ }
function handleUserTemp() { /* ... */ }
function processDataNew() { /* ... */ }
function processDataOld() { /* ... */ }
```

### Documentation Slop

#### Rigid Template Following
```markdown
## Component Name

### Overview
This component provides...

### Key Features
- Feature 1
- Feature 2
- Feature 3

### Usage
To use this component...

### Examples
Here's an example...

### API Reference
The following methods...

### Best Practices
When using this component...

### Troubleshooting
If you encounter...
```

#### Unnecessary Categorization
```markdown
## Configuration

### Basic Configuration
#### Essential Settings
##### Primary Options
- Option 1
  - Sub-option 1.1
    - Detail 1.1.1
    - Detail 1.1.2
  - Sub-option 1.2
##### Secondary Options
```

## Verification Commands

### Bold Bullet Detection (PRIORITY ONE)
```bash
# Find the classic bold-colon pattern
grep -r "^\s*[-*•→▸▪︎]\s*\*\*[^:]*:\*\*" --include="*.md" --include="*.txt"

# Find numbered lists with bold patterns
grep -r "^[0-9]\+\.\s*\*\*[^:]*:\*\*" --include="*.md"

# Count bold bullet occurrences per file (high numbers = AI slop)
for f in *.md; do echo "$f: $(grep -c "^\s*[-*]\s*\*\*.*:\*\*" "$f" 2>/dev/null || echo 0)"; done | sort -t: -k2 -rn

# Find all variations of bold patterns
grep -r "\*\*[A-Z][^:]*:\*\*" --include="*.md" | head -20

# Detect "Enables/Provides/Allows" pattern starts
grep -r "^\s*[-*]\s*\*\*.*:\*\*\s*\(Enables\|Provides\|Allows\|Offers\|Delivers\|Ensures\)" --include="*.md"
```

### Text Pattern Scanning  
```bash
# Find AI phrase indicators
grep -r "Furthermore,\|Moreover,\|It's worth noting\|In essence\|Comprehensive solution\|Robust implementation" --include="*.md" --include="*.txt"

# Find excessive qualifiers
grep -r "may\|might\|could\|possibly\|potentially\|can\|should" --include="*.js" --include="*.ts" | grep -E "(may|might|could).*(may|might|could)"

# Find numbered function variations
grep -r "function.*[0-9]\|function.*Temp\|function.*New\|function.*Old" --include="*.js" --include="*.ts"
```

### Comment Analysis
```bash
# Find over-commented code
awk '/\/\// { comments++ } END { print "Comment lines:", comments }' *.js

# Find obvious comments
grep -r "// Initialize\|// Increment\|// Decrement\|// Return\|// Check if" --include="*.js" --include="*.ts"

# Find refactor traces
grep -r "// Updated\|// Refactored\|// Now uses\|// Changed to\|// Modified" --include="*.js" --include="*.ts"

# Find excessive JSDoc
grep -A5 "/\*\*" --include="*.js" | grep -E "@param.*obvious|@returns.*value"
```

### Structure Analysis
```bash
# Find excessive try-catch blocks
grep -c "try {" *.js | sort -t: -k2 -rn | head -10

# Find defensive null checks
grep -r "=== null.*=== undefined\|!= null.*!= undefined" --include="*.js"

# Find template following in markdown
grep -r "## Overview" --include="*.md" | wc -l
```

## Slop Scoring System

### 🔴 **CRITICAL SLOP** (Immediate Refactoring Needed)
- Bold bullet patterns ("**Term:** Description") throughout documentation
- Every function has a comment explaining what it does
- Numbered function names (func1, func2, func3)
- Triple-nested bullet points in documentation
- "Furthermore/Moreover" in every paragraph
- Comments explaining language syntax
- More than 5 bold-colon bullets in a single document section

### 🟡 **HIGH SLOP** (Significant AI Patterns)
- Excessive use of "comprehensive," "robust," "elegant"
- Over-qualified statements (may, might, could everywhere)
- Rigid template structure across all docs
- Defensive programming without justification
- Lists where every item starts with the same verb

### 🟠 **MEDIUM SLOP** (Moderate AI Influence)
- Unnecessary categorization depth
- Generic section headers everywhere
- Some obvious code comments
- Occasional "It's worth noting"
- Try-catch around safe operations

### 🟢 **LOW SLOP** (Minor AI Traces)
- Slightly verbose explanations
- Occasional unnecessary comments
- Some template following
- Minor over-organization

## Output Format

### When AI Slop Detected:

```
🤖 AI SLOP REPORT - ARTIFICIAL PATTERNS DETECTED 🤖

📊 Slop Summary:
  🔴 Critical Slop: 8 instances
  🟡 High Priority: 15 instances
  🟠 Medium Priority: 23 instances
  🟢 Low Priority: 31 instances

🔴 CRITICAL SLOP FINDINGS:

1. BOLD BULLET EPIDEMIC
   File: README.md
   Count: 47 instances of "**Term:** Description" pattern
   Example:
     - **Installation:** Steps to install the package
     - **Configuration:** How to configure the settings
     - **Usage:** Instructions for using the tool
   Why it's slop: No human writes documentation this robotically
   
2. EXCESSIVE OBVIOUS COMMENTS
   File: src/utils/calculator.js
   Lines: 23-45
   Pattern: Every single line has a comment explaining basic operations
   Example:
     let x = 0;  // Initialize x to zero
     x++;        // Increment x by one
   
3. AI REFACTOR TRACES
   File: src/api/handler.js
   Pattern: Comments documenting AI changes
   Example:
     // processRequest function (refactored for clarity)
     // Now uses async/await pattern (improved from callbacks)

🟡 HIGH PRIORITY SLOP:

1. PHRASE OVERUSE
   File: docs/architecture.md
   Count: "Furthermore" (8x), "Moreover" (6x), "Robust" (12x)
   
2. DEFENSIVE OVERLOAD
   File: src/validator.js:67-125
   Pattern: Null checks for internal functions that never receive null

[... continue with all findings ...]

📝 REFACTORING RECOMMENDATIONS:

1. ❗ ELIMINATE ALL BOLD BULLET PATTERNS
   Before: - **Feature:** This feature does X
   After: The feature does X
   Or just: - Feature X
   
2. ❗ Remove all obvious comments (save 200+ lines)
3. ❗ Convert forced bullet lists to natural paragraphs
4. ❗ Consolidate numbered functions into single parameterized function
5. ⚠️ Remove unnecessary null checks
6. ⚠️ Replace "Furthermore/Moreover" with natural transitions
7. ⚠️ Unindent excessive categorization

🎯 AI SLOP SCORE: 73% - HIGHLY ARTIFICIAL

This codebase shows significant AI generation patterns.
Estimated human editing needed: 4-6 hours
```

### When Minimal Slop Found:

```
✅ AI SLOP REPORT - REFRESHINGLY HUMAN ✅

📊 Analysis Summary:
  Files Scanned: 127
  Comments: Purposeful and minimal
  Documentation: Natural and varied structure
  Code: Clean without over-explanation

✅ Human Patterns Detected:
  ✓ Inconsistent but practical documentation
  ✓ Comments only where truly needed
  ✓ Natural language variation
  ✓ No template rigidity
  ✓ Pragmatic error handling

⚠️ Minor AI Traces:
  - 2 instances of "It's worth noting"
  - Some sections could be more concise
  - Found one "comprehensive solution" phrase

🎯 AI SLOP SCORE: 8% - AUTHENTICALLY HUMAN

Code appears naturally written with minimal AI generation.
```

## Configuration

Support `.aisloprc` configuration:

```json
{
  "customPatterns": [
    "cutting-edge",
    "state-of-the-art",
    "best-in-class"
  ],
  "ignoreFiles": [
    "*.min.js",
    "vendor/*",
    "node_modules/*"
  ],
  "strictness": "high",
  "includeMetrics": true
}
```

## Usage Examples

```bash
# Full slop analysis
/ai-slop

# Check only documentation
/ai-slop docs

# Check specific directory
/ai-slop src/components

# Check only comments
/ai-slop comments

# Maximum strictness
/ai-slop --strict
```

## Special Detection: LLM-Specific Patterns

### ChatGPT Signatures
- "Certainly! Here's..."
- "Great question!"
- Markdown code blocks with language tags for everything
- Numbered lists for every explanation

### Claude Signatures
- Thoughtful hedging ("might be worth considering")
- "I should note that..."
- Breaking everything into clear sections

### Copilot Signatures
- Incomplete implementations with TODO
- Comments that trail off with "..."
- Suggested imports that don't exist

## Refactoring Bold Bullets: Before and After

### Example 1: Documentation
```markdown
# AI SLOP VERSION:
## Features
- **Authentication:** Provides secure user authentication with JWT tokens
- **Authorization:** Enables role-based access control for resources  
- **Session Management:** Handles user sessions with Redis backing

# HUMAN VERSION:
## Features
We handle authentication using JWT tokens, with role-based access control
and Redis-backed session management.

# OR EVEN SIMPLER:
## Features
- JWT authentication
- Role-based access control
- Redis sessions
```

### Example 2: Configuration
```markdown
# AI SLOP VERSION:
- **Database:** PostgreSQL for persistent data storage
- **Cache:** Redis for high-performance caching layer
- **Queue:** RabbitMQ for asynchronous job processing

# HUMAN VERSION:
The system uses PostgreSQL for data storage, Redis for caching, 
and RabbitMQ for job processing.
```

## Final Instructions

1. **PRIORITY ONE:** Hunt down and eliminate bold bullet patterns
2. Focus on patterns, not individual instances
3. Look for repetition across files
4. Check git history for bulk AI-generated commits
5. Identify template following versus natural variation
6. Flag formulaic structure over organic growth
7. Detect when comments explain the language, not the logic
8. Find defensive patterns without justification
9. Recognize theatrical adjectives and corporate speak
10. Remember: Good documentation reads like a human wrote it

The goal: Help developers identify and remove artificial patterns to create more authentic, maintainable code. The bold bullet pattern is the most obvious tell - if you see it everywhere, the document is AI slop.