import asyncio
from typing import List, Optional, Dict
import json
import re
import chainlit as cl
from agents import Agent, Runner
from client import model
from openai.types.responses import ResponseTextDeltaEvent
from search_tools import tavily_crawl_tool, tavily_extract_tool, tavily_search_tool

# ===== SPECIALIST AGENTS =====

market_analyst_agent = Agent(
        name="MarketAnalyst",
        instructions="""
        You are a market analyst. Based on the startup information provided, analyze:
        1. Estimated market size (TAM) for this category
        2. Key competitors in this space
        3. Market gaps and opportunities
        4. Target customer segments
        5. Industry trends

        Keep analysis CONCISE (max 300 words). Focus on what matters for investors.
        """,
        model=model,
        tools=[
            tavily_search_tool,
            tavily_extract_tool,
            tavily_crawl_tool
        ]
    )


product_strategist_agent = Agent(
        name="ProductStrategist",
        instructions="""
        You are a product strategist. Based on the startup information, define:
        1. Core value proposition (one sentence)
        2. Main problem it solves
        3. MVP features
        4. Key differentiators vs competitors (use search tools to research competitors)
        5. Future roadmap (Phase 2, Phase 3)

        Use the search tools when you need to research competitors or related products in the market.
        Keep it CONCISE (max 250 words). Focus on customer outcomes.
        """,
        model=model,
        tools=[
            tavily_search_tool,
            tavily_extract_tool,
            tavily_crawl_tool
        ]
    )


business_model_agent = Agent(
        name="BusinessModelAnalyst",
        instructions="""
        You are a business model expert. Design:
        1. Pricing model (subscription, freemium, tiered, etc)
        2. Suggested price tiers (research competitor pricing)
        3. Unit economics (CAC, LTV, ratio, payback period)
        4. Revenue projections
        5. Break-even timeline

        Use search tools to research competitor pricing models and industry benchmarks.
        Keep it CONCISE (max 250 words). Show the math. Be conservative.
        """,
        model=model,
        tools=[
            tavily_search_tool,
            tavily_extract_tool,
            tavily_crawl_tool
        ]
    )


gtm_strategist_agent = Agent(
        name="GoToMarketStrategist",
        instructions="""
        You are a GTM expert. Plan:
        1. Ideal Customer Profile (ICP)
        2. Primary distribution channels (2-3) - research where similar companies distribute
        3. Phase 1 tactics to get first 100 customers
        4. Phase 2 scaling strategy - look up similar company growth strategies
        5. Key milestones and metrics

        Use search tools to research distribution channels and tactics used by similar companies.
        Keep it CONCISE (max 250 words). Be specific and tactical.
        """,
        model=model,
        tools=[
            tavily_search_tool,
            tavily_extract_tool,
            tavily_crawl_tool
        ]
    )


financial_analyst_agent = Agent(
        name="FinancialAnalyst",
        instructions="""
        You are a financial analyst. Project:
        1. 12-month customer growth (conservative) - research market benchmarks
        2. Monthly revenue projections
        3. Operating expense estimates - research industry benchmarks
        4. Burn rate and runway
        5. Profitability timeline
        6. Key financial assumptions

        Use search tools to find market benchmarks and financial metrics for similar companies.
        Keep it CONCISE (max 250 words). Show assumptions and math.
        """,
        model=model,
        tools=[
            tavily_search_tool,
            tavily_extract_tool,
            tavily_crawl_tool
        ]
    )


exec_summary_agent = Agent(
        name="ExecutiveSummaryWriter",
        instructions="""
        You are a business storyteller. Write a 1-page executive summary with:
        1. Problem statement (what's broken)
        2. Solution (clear and simple)
        3. Market opportunity (TAM, growth) - research market size and growth
        4. Why now (timing) - look for industry trends
        5. Why this team will win (competitive advantage) - research competitive landscape
        6. Business model and path to profitability

        Use search tools to validate market size, growth, and competitive advantages.
        Keep it CONCISE (max 400 words). Write like a journalist - clear, compelling, no jargon.
        """,
        model=model,
        tools=[
            tavily_search_tool,
            tavily_extract_tool,
            tavily_crawl_tool
        ]
    )

# ===== UNIFIED BUSINESS PLAN GENERATOR =====

business_plan_generator_agent = Agent(
        name="BusinessPlanGenerator",
        model=model,
        tools=[
            market_analyst_agent.as_tool(tool_name="analyze_market", tool_description="Analyze market and competitors"),
            product_strategist_agent.as_tool(tool_name="define_product", tool_description="Define product strategy"),
            business_model_agent.as_tool(tool_name="design_revenue_model", tool_description="Design business model"),
            gtm_strategist_agent.as_tool(tool_name="plan_gtm", tool_description="Plan go-to-market"),
            financial_analyst_agent.as_tool(tool_name="project_financials", tool_description="Project financials"),
            exec_summary_agent.as_tool(tool_name="write_summary", tool_description="Write executive summary"),
        ],
        instructions="""
        You are a business plan generator. Your role has two phases:
        1. Information Gathering Phase: Collect 4 specific pieces of information about the startup:
           - Startup name
           - What it does (idea/problem it solves)
           - Target market (who uses it)
           - Key features (core capabilities)
           
           Instructions during information gathering:
           - If user provides info, acknowledge it and ask for missing pieces
           - Ask only ONE question per response
           - Format your response with the information you have collected so far
           - Be friendly, concise, and efficient

        2. Business Plan Generation Phase: Once you have all 4 pieces of information, generate a comprehensive business plan by calling specialist agents.

        Instructions for business plan generation:
        - Call each specialist agent to generate their section
        - Compile all sections into a professional business plan
        - Follow the proper business plan format

        PROCESS for business plan generation:
        1. Call analyze_market_agent to get market analysis
        2. Call define_product_agent to get product strategy
        3. Call design_revenue_model_agent to get business model
        4. Call plan_gtm_agent to get GTM strategy
        5. Call project_financials_agent to get financial projections
        6. Call write_summary_agent to get executive summary
        7. Compile all into the final business plan

        FORMAT YOUR BUSINESS PLAN OUTPUT AS:
        # Business Plan: [Startup Name]

        ## Executive Summary
        [Executive summary content here]

        ## Market Analysis & Opportunity
        [Market analysis here]

        ## Product & Solution
        [Product strategy here]

        ## Business Model & Revenue Strategy
        [Business model here]

        ## Go-to-Market Strategy
        [GTM strategy here]

        ## Financial Projections & Unit Economics
        [Financial projections here]

        Make it professional, concise, and focused on what matters to investors.
        """
    )