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
        # Create empty message and send it
        msg = cl.Message(content="")
        await msg.send()

        # Create a status message to show ongoing activities
        status_msg = cl.Message(content="🔄 Starting business plan generation...")
        await status_msg.send()

        # Prepare the startup information for the agent
        startup_context = f"""
        Generate a comprehensive business plan with the following startup information:
        - Name: {startup_info.get('name', 'Not provided')}
        - Idea: {startup_info.get('idea', 'Not provided')}
        - Target Market: {startup_info.get('target_market', 'Not provided')}
        - Key Features: {startup_info.get('key_features', 'Not provided')}
        """

        # Run the business plan generator with streaming
        result = Runner.run_streamed(
            business_plan_generator_agent,
            startup_context
        )

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
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                if event.data.delta:  # Only stream non-empty deltas
                    await msg.stream_token(event.data.delta)
            
            # Update status when tool calls are detected
            elif event.type == "raw_response_event":
                if hasattr(event.data, 'type'):
                    if event.data.type == 'response.output_item.added':
                        # Check if this is a function/tool call
                        if hasattr(event.data, 'item') and hasattr(event.data.item, 'name'):
                            tool_name = event.data.item.name
                            current_tool = tool_name
                            status_text = tool_status_messages.get(tool_name, f"🔄 Executing {tool_name}...")
                            await status_msg.update(content=status_text)
            
            # Update status when tool calls finish
            elif event.type == "run_item_stream_event":
                if hasattr(event, 'item') and event.item.type == "tool_call_item":
                    # Tool call started
                    tool_name = getattr(event, 'name', 'unknown')
                    if tool_name and tool_name in tool_status_messages:
                        current_tool = tool_name
                        status_text = tool_status_messages[tool_name]
                        await status_msg.update(content=status_text)
                elif hasattr(event, 'item') and event.item.type == "tool_call_output_item":
                    # Tool call completed - update status
                    completed_tool = current_tool
                    if completed_tool:
                        await status_msg.update(content=f"✅ Completed {completed_tool.replace('_', ' ').title()}... Starting next phase...")

        # Update message to finalize it
        await msg.update()
        # Remove the status message
        await status_msg.remove()

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
        # Check if we already have all the required information
        all_info_present = all([
            startup_info.get("name"),
            startup_info.get("idea"),
            startup_info.get("target_market"),
            startup_info.get("key_features")
        ])

        if all_info_present:
            # If we already have all information, generate the business plan directly
            await business_plan_generation(startup_info=startup_info)

            # Reset for new conversation
            cl.user_session.set("conversation_history", [])
            cl.user_session.set("startup_info", {
                "name": None,
                "idea": None,
                "target_market": None,
                "key_features": None,
            })
        else:
            # We're still in information gathering phase
            # Create a context string that includes current startup info and user message
            context_message = f"""
            Current startup information gathered:
            - Name: {startup_info.get('name', 'Not provided')}
            - Idea: {startup_info.get('idea', 'Not provided')}
            - Target Market: {startup_info.get('target_market', 'Not provided')}
            - Key Features: {startup_info.get('key_features', 'Not provided')}

            Latest user message: {user_message}

            Your task:
            1. If the user is providing startup information, acknowledge it and ask for any missing pieces.
            2. If all required information is available (name, idea, target market, key features), generate the complete business plan.
            3. If information is missing, ask for the specific missing piece.
            """

            # Run the unified business plan generator agent
            result = await Runner.run(
                business_plan_generator_agent,
                context_message
            )

            response = result.final_output

            # Check if response contains a business plan (indicating generation phase)
            if "# Business Plan:" in response:
                # We have a complete business plan, send it to the user
                await cl.Message(content=response).send()
                
                # Reset for new conversation
                cl.user_session.set("conversation_history", [])
                cl.user_session.set("startup_info", {
                    "name": None,
                    "idea": None,
                    "target_market": None,
                    "key_features": None,
                })
            else:
                # We're still in information gathering phase, send the agent's response
                await cl.Message(content=response).send()
                conversation_history.append({"role": "assistant", "content": response})
                cl.user_session.set("conversation_history", conversation_history)

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