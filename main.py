"""
main.py - Chainlit chatbot with streaming support using unified agent
Shows live progress as agents work
"""

import asyncio
import chainlit as cl
from custom_agents import business_plan_generator_agent
from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent


@cl.on_chat_start
async def start():
    """Initialize the chatbot"""
    cl.user_session.set("conversation_history", [])
    cl.user_session.set("startup_info", {
        "name": None,
        "idea": None,
        "target_market": None,
        "key_features": None,
    })

    await cl.Message(content="""
🚀 **Welcome to the Business Plan Generator!**

I'll help you create a comprehensive SaaS business plan.
Tell me about your startup idea, and I'll gather the necessary information to create your business plan.

Let's get started! 💡
    """).send()


async def business_plan_generation(startup_info: dict):
    """Generate business plan with proper Chainlit streaming and status updates"""

    try:
        # Prepare the startup information for the agent
        startup_context = f"""
        Generate a comprehensive business plan with the following startup information:
        - Name: {startup_info.get('name', 'Not provided')}
        - Idea: {startup_info.get('idea', 'Not provided')}
        - Target Market: {startup_info.get('target_market', 'Not provided')}
        - Key Features: {startup_info.get('key_features', 'Not provided')}
        """

        # This function can be called if we need to specifically generate a plan
        # with pre-collected information, though our main flow handles this in one call
        pass

    except Exception as e:
        error_msg = str(e)
        await cl.Message(content=f"❌ Error generating plan: {error_msg}").send()


@cl.on_message
async def main(message: cl.Message):
    """Handle all conversations with the unified agent"""

    user_message = message.content
    conversation_history = cl.user_session.get("conversation_history", [])
    startup_info = cl.user_session.get("startup_info", {
        "name": None,
        "idea": None,
        "target_market": None,
        "key_features": None,
    })

    # Add user message to history
    conversation_history.append({"role": "user", "content": user_message})
    cl.user_session.set("conversation_history", conversation_history)

    try:
        # Create a context string that includes current startup info and user message
        # Format startup information as a single string that the agent can use when calling specialist tools
        # Use | as a separator to avoid comma interpretation as argument separators
        startup_info_str = f"Startup Name: {startup_info.get('name', 'Not provided')} | Idea: {startup_info.get('idea', 'Not provided')} | Target Market: {startup_info.get('target_market', 'Not provided')} | Key Features: {startup_info.get('key_features', 'Not provided')}"
        
        context_message = f"""
        Current startup information gathered: {startup_info_str}

        Latest user message: {user_message}

        Your task:
        1. If the user is providing startup information, acknowledge it and ask for any missing pieces.
        2. If all required information is available (name, idea, target market, key features), generate the complete business plan by calling each specialist agent with this EXACT format: "{startup_info_str}"
        3. If information is missing, ask for the specific missing piece.

        IMPORTANT: When calling specialist agents, pass the startup information as a single string using the exact format shown above with | as separators.
        """

        # Run the unified business plan generator with a single streaming call for both phases
        result = Runner.run_streamed(
            business_plan_generator_agent,
            context_message
        )

        # Create a status message for the process
        msg = cl.Message(content="🔄 Processing your request...")
        await msg.send()

        # Track which specialist agent is currently being called
        current_tool = None
        tool_status_messages = {
            "analyze_market": "🔍 Researching market trends and competitors...",
            "define_product": "💡 Defining product strategy and value proposition...",
            "design_revenue_model": "💰 Designing business model and pricing strategy...",
            "plan_gtm": "🎯 Planning go-to-market strategy...",
            "project_financials": "📊 Projecting financials and unit economics...",
            "write_summary": "📝 Writing executive summary..."
        }

        # Stream events as they arrive
        async for event in result.stream_events():
            # Handle text deltas for the main response
            if event.type == "raw_response_event":
                if hasattr(event.data, 'type'):
                    if event.data.type == 'response.text.delta':
                        if hasattr(event.data, 'delta') and event.data.delta:
                            await msg.stream_token(event.data.delta)
                    elif event.data.type == 'response.output_item.added':
                        # Check if this is a function/tool call
                        if hasattr(event.data, 'item') and hasattr(event.data.item, 'name'):
                            tool_name = event.data.item.name
                            current_tool = tool_name
                            status_text = tool_status_messages.get(tool_name, f"🔄 Processing: {tool_name}...")
                            msg.content = status_text
                            await msg.update()

            # Handle when run items happen (tool calls, outputs, etc.)
            elif event.type == "run_item_stream_event":
                if hasattr(event, 'item'):
                    if event.item.type == "tool_call_item":
                        # Tool call started
                        tool_name = getattr(event, 'name', 'unknown')
                        if tool_name and tool_name in tool_status_messages:
                            current_tool = tool_name
                            msg.content = tool_status_messages[tool_name]
                            await msg.update()
                    elif event.item.type == "tool_call_output_item":
                        # Tool call completed - update status
                        if current_tool:
                            msg.content = f"✅ Completed {current_tool.replace('_', ' ').title()}... Generating next section..."
                            await msg.update()
                    elif event.item.type == "message_output_item":
                        # Handle message output items
                        try:
                            from agents import ItemHelpers
                            message_content = ItemHelpers.text_message_output(event.item)
                            await msg.stream_token(message_content)
                        except:
                            # Fallback if ItemHelpers is not available or fails
                            pass

        # Final update to the message
        await msg.update()

        # Get the final response content
        response = msg.content

        # Check if response contains a business plan (indicating generation phase)
        if "# Business Plan:" in response:
            # We have a complete business plan, reset session
            cl.user_session.set("conversation_history", [])
            cl.user_session.set("startup_info", {
                "name": None,
                "idea": None,
                "target_market": None,
                "key_features": None,
            })

    except Exception as e:
        await cl.Message(content=f"""
❌ **Error:**

{str(e)}

Please try again or provide more details about your startup.
        """).send()


@cl.on_chat_end
def end():
    """Clean up when chat ends"""
    cl.user_session.set("conversation_history", None)
    cl.user_session.set("startup_info", None)
    print("Chat ended")


if __name__ == "__main__":
    # Run: chainlit run main.py
    pass