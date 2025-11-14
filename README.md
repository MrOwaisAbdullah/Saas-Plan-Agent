# SaaS Business Plan Agent

A conversational SaaS Business Plan Generator that uses the OpenAI Agents SDK and Chainlit to collect startup information and generate investor-focused business plans. The agent implements a unified flow that gathers essential inputs, calls specialist agents for market research, product strategy, business modeling, go-to-market planning, and financial projections, and returns a structured plan.

Key features
- Unified conversational flow for information gathering and plan generation
- Specialist agents for Market, Product, Business Model, GTM, Financials, and Executive Summary
- Integrates with search tools (Tavily) for live research when available
- Built with the OpenAI Agents SDK and Chainlit for interactive streaming responses
- Uses the 6-Part Prompting Framework to make prompts precise and effective

Getting started
Prerequisites
- Python 3.10+
- An OpenAI-compatible Agents SDK (this project expects the `agents` package)
-- Chainlit for the chat UI: `uv add chainlit`
- (Optional) Tavily API key for live web research: set `TAVILY_API_KEY` in your environment

Install dependencies

```powershell
# using the `uv` package manager
uv sync
```



Environment
- `OPENAI_API_KEY` (for tracing or the key for your chosen model provider)
- `TAVILY_API_KEY` (optional) — when present, the agent can perform live web searches and extraction

Run the agent locally (Chainlit)

```powershell
# start the chainlit app
uv run chainlit run main.py
```

How it works
- Conversation start: The agent greets the user and collects four core pieces of startup information: `Startup Name`, `Idea/Problem`, `Target Market`, and `Key Features`.
- Information gathering: The unified `business_plan_generator_agent` asks for missing pieces one at a time and acknowledges provided info.
- Plan generation: After collecting all four items, the orchestrator calls specialist agents in sequence: Market, Product, Business Model, GTM, Financials, Executive Summary.
- Output: The final business plan is returned as a structured, investor-focused document with the following sections:
	- Executive Summary
	- Market Analysis & Opportunity
	- Product & Solution
	- Business Model & Revenue Strategy
	- Go-to-Market Strategy
	- Financial Projections & Unit Economics

Prompting philosophy: the 6-part framework
This project embraces the 6-Part Prompting Framework to get professional-level results from large language models. The framework encourages prompts that include:
- Command: a clear action verb (e.g., "Generate", "Analyze", "Design")
- Context: relevant background and constraints (who, what, when)
- Logic: the output structure and reasoning steps you want the model to follow
- Roleplay: the expert persona or voice the model should adopt
- Formatting: exact output format (headers, tables, bullet points)
- Questions: the final step asking the model to generate clarifying questions to refine outputs

Examples
- Quick prompt example to the agent (done automatically by the conversation flow):

```
You are a SaaS business plan expert. Collect these four pieces of information: Startup Name, Idea/Problem, Target Market, Key Features. Ask for one missing item per message. Once all 4 are provided, generate a full investor-ready SaaS business plan with sections for Executive Summary, Market Analysis, Product & Solution, Business Model, GTM, and Financials.
```

Customization
- Specialist agents (in `custom_agents.py`) can be tuned for tone, length, and tool usage.
- Search tools are pluggable; `search_tools.py` contains wrappers for Tavily — replace or extend if you prefer another web-research provider.

Development notes
- `client.py` contains model configuration for the OpenAI Agents SDK. Adjust `model` or client settings to match your provider.
- `main.py` contains the Chainlit handlers and streaming logic that present progress and tool-call updates in the UI.
- The orchestrator (`business_plan_generator_agent` in `custom_agents.py`) passes startup info as a single pipe-separated string to specialist tools to avoid argument-parsing issues.

Troubleshooting
- If you get an import error for `tavily` or missing `TAVILY_API_KEY`, the repo can still run — the search tools will fall back to no-op responses (see `search_tools.py`).

Contributing
- Improve the specialist agent prompts to match your investor style or domain
- Add integrations for additional research tools or data sources
- Enhance Chainlit UI with custom components or templates

License
This repository contains example code and is provided as-is. Verify licensing for third-party packages before production use.

