# Delegate Tasks to Gemini

## Goal

To leverage Gemini AI for specific tasks like code review, design analysis, brainstorming, or getting alternative perspectives on technical decisions. This command provides a seamless way for Claude to outsource certain thinking work or get a second opinion from another AI model.

## Input

Task description or prompt: $ARGUMENTS (e.g., "Review this function for performance", "Analyze this architecture pattern")
- The task description should be clear and specific
- Can include references to files or code that will be included in context

## Process

1. **Parse Task Request:** Extract the task description from arguments
2. **Gather Context:** Identify and read any referenced files or code snippets
3. **Format Prompt:** Create a well-structured prompt for Gemini including:
   - Clear task description
   - Relevant context (code, files, requirements)
   - Specific questions or areas of focus
4. **Execute Gemini:** Run `gemini -p` with the formatted prompt
5. **Process Response:** Parse Gemini's output and format for presentation
6. **Present Results:** Display Gemini's insights in a clear, actionable format

## Task Types

### 1. Code Review
Request Gemini to review code for:
- Performance optimization opportunities
- Security vulnerabilities
- Code quality and best practices
- Refactoring suggestions
- Design pattern improvements

### 2. Design Analysis
Get Gemini's perspective on:
- Architecture decisions
- Design pattern choices
- System design trade-offs
- Scalability considerations
- Technology stack evaluation

### 3. Brainstorming
Leverage Gemini for:
- Edge case identification
- Feature enhancement ideas
- Problem-solving approaches
- Alternative implementation strategies
- Testing scenarios

### 4. Documentation Review
Have Gemini analyze:
- API documentation clarity
- README completeness
- Code comment quality
- User guide effectiveness

## Prompt Formatting

### Basic Structure
```
Task: [Clear task description]

Context:
[Relevant code, files, or background information]

Specific Focus:
[Particular aspects to analyze or questions to answer]

Please provide:
1. [Specific deliverable 1]
2. [Specific deliverable 2]
3. [Specific deliverable 3]
```

### Code Review Example
```
Task: Review the following authentication middleware for security vulnerabilities and performance

Context:
[Code snippet from auth.js]

Specific Focus:
- JWT token validation security
- Error handling completeness
- Performance bottlenecks
- Best practices compliance

Please provide:
1. Security vulnerabilities found (if any)
2. Performance improvement suggestions
3. Code quality recommendations
4. Overall assessment
```

### Design Analysis Example
```
Task: Analyze the proposed microservices architecture for an e-commerce platform

Context:
[Architecture diagram description or design document excerpt]

Specific Focus:
- Service boundaries appropriateness
- Communication patterns efficiency
- Data consistency approach
- Scalability potential

Please provide:
1. Strengths of the current design
2. Potential issues or bottlenecks
3. Alternative approaches to consider
4. Recommended improvements
```

## Execution Flow

1. **Validate Gemini Availability**
   ```bash
   which gemini || echo "Gemini CLI not found"
   ```

2. **Prepare Prompt File (if needed)**
   For complex prompts, create a temporary file:
   ```bash
   cat > /tmp/gemini_prompt.txt << 'EOF'
   [Formatted prompt content]
   EOF
   ```

3. **Execute Gemini Command**
   ```bash
   gemini -p "[prompt]"
   # Or for file-based prompt:
   gemini -p "$(cat /tmp/gemini_prompt.txt)"
   ```

4. **Handle Response**
   - Capture output
   - Check for errors
   - Format for display

## Context Gathering

When the task references specific files or code:

1. **Explicit File References**
   - Look for file paths in the task description
   - Read and include file contents in the prompt

2. **Implicit Context**
   - If reviewing "current changes", get `git diff`
   - If analyzing "this function", find the most recently discussed function
   - If evaluating "the architecture", look for design docs

3. **Context Limits**
   - Include only relevant portions of large files
   - Summarize extensive documentation
   - Focus on the specific area of interest

## Output Format

### Success Response
```
🤖 Gemini Analysis Results

📋 Task: [Original task description]

🔍 Analysis:
[Gemini's structured response]

💡 Key Insights:
• [Insight 1]
• [Insight 2]
• [Insight 3]

🎯 Recommendations:
1. [Actionable recommendation 1]
2. [Actionable recommendation 2]
3. [Actionable recommendation 3]

📌 Next Steps:
[Suggested actions based on Gemini's analysis]
```

### Error Response
```
❌ Gemini Delegation Failed

🔍 Issue: [Error description]

💡 Troubleshooting:
• Check if Gemini CLI is installed: `which gemini`
• Verify credentials are loaded
• Ensure prompt is properly formatted

🔄 Alternative Actions:
[Suggestions for completing the task without Gemini]
```

## Error Handling

1. **Gemini Not Installed**
   - Inform user that Gemini CLI is not available
   - Provide installation instructions if possible
   - Offer to complete the task without Gemini

2. **Authentication Issues**
   - Check for credential errors in output
   - Suggest credential refresh steps
   - Provide fallback approach

3. **Timeout or Network Issues**
   - Implement reasonable timeout (30 seconds)
   - Retry once on failure
   - Report network issues clearly

4. **Invalid Response**
   - Handle empty or malformed responses
   - Attempt to extract partial insights
   - Provide context about the failure

## Advanced Features

### 1. Iterative Refinement
Allow follow-up questions to Gemini:
```
Initial: /gemini "Review this API design"
Follow-up: /gemini "Can you elaborate on the rate limiting suggestion?"
```

### 2. Comparison Mode
Get Gemini's perspective on alternatives:
```
/gemini "Compare these two implementation approaches: [approach A] vs [approach B]"
```

### 3. Validation Mode
Use Gemini to validate Claude's suggestions:
```
/gemini "Validate this solution for [problem]: [proposed solution]"
```

## Integration Guidelines

1. **When to Use Gemini**
   - Need a second opinion on complex decisions
   - Want alternative approaches to a problem
   - Require specialized analysis (security, performance)
   - Benefit from different perspective on design

2. **When NOT to Use Gemini**
   - Simple, straightforward tasks
   - Tasks requiring deep project context
   - Time-sensitive operations
   - Tasks better suited for human review

3. **Complementary Workflow**
   - Claude handles implementation
   - Gemini provides review/analysis
   - User makes final decisions
   - Both AIs work together effectively

## Configuration

Environment variables that affect behavior:
- `GEMINI_TIMEOUT`: Maximum wait time for Gemini response (default: 30s)
- `GEMINI_MAX_CONTEXT`: Maximum characters to include in context (default: 10000)
- `GEMINI_RETRY_COUNT`: Number of retries on failure (default: 1)

## Usage Examples

```bash
# Basic code review
/gemini "Review the error handling in src/api/auth.js"

# Architecture analysis
/gemini "Analyze the microservices design in docs/architecture.md for scalability"

# Brainstorming session
/gemini "Help identify edge cases for the user registration flow"

# Performance consultation
/gemini "Suggest performance optimizations for the database query in src/models/user.js:45"

# Security audit
/gemini "Check this authentication flow for security vulnerabilities"
```

## Final Instructions

1. Always format prompts clearly with context and specific asks
2. Handle errors gracefully and provide alternatives
3. Present Gemini's insights in an actionable format
4. Maintain clear attribution (this is Gemini's analysis)
5. Use Gemini as a complementary tool, not a replacement
6. Respect timeout limits to avoid hanging
7. Filter and summarize verbose responses
8. Validate that Gemini's suggestions align with project constraints
9. Provide clear next steps based on the analysis
10. Keep the interaction focused and goal-oriented