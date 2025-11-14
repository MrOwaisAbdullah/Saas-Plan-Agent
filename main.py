"""
main.py - Chainlit chatbot with streaming support using unified agent
Shows live progress as agents work
"""

import asyncio
import chainlit as cl
from custom_agents import business_plan_generator_agent
from agents import Runner, SQLiteSession
from openai.types.responses import ResponseTextDeltaEvent


@cl.on_chat_start
async def start():
    """Initialize the chatbot"""
    # Create a session for maintaining conversation history
    # Using unique session ID per user conversation
    import uuid
    session_id = f"conversation_{uuid.uuid4().hex[:8]}"
    session = SQLiteSession(session_id)
    cl.user_session.set("session", session)
    
    cl.user_session.set("startup_info", {
        "name": None,
        "idea": None,
        "target_market": None,
        "key_features": None,
    })

    await cl.Message(content="""
🚀 **Welcome to the SaaS Business Plan Generator!**

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
    session = cl.user_session.get("session")
    startup_info = cl.user_session.get("startup_info", {
        "name": None,
        "idea": None,
        "target_market": None,
        "key_features": None,
    })

    try:
        # The agent is designed to handle the conversation flow, so we just send the user's message.
        # The agent's instructions will guide it to either gather more information or generate the plan.
        result = Runner.run_streamed(
            business_plan_generator_agent,
            user_message,
            session=session
        )

        # Create a status message for the process
        status_msg = cl.Message(content="🔄 Processing your request...")
        await status_msg.send()

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

        # Store the final response content
        final_response_content = ""

        # Stream events as they arrive
        async for event in result.stream_events():
            # Handle text deltas for the main response
            if event.type == "raw_response_event":
                if hasattr(event.data, 'type'):
                    if event.data.type == 'response.text.delta':
                        if hasattr(event.data, 'delta') and event.data.delta:
                            # Add to final response content for later use
                            final_response_content += event.data.delta
                            await status_msg.stream_token(event.data.delta)
                    elif event.data.type == 'response.output_item.added':
                        # Check if this is a function/tool call
                        if hasattr(event.data, 'item') and hasattr(event.data.item, 'name'):
                            tool_name = event.data.item.name
                            current_tool = tool_name
                            status_text = tool_status_messages.get(tool_name, f"🔄 Processing: {tool_name}...")
                            status_msg.content = status_text
                            await status_msg.update()

            # Handle when run items happen (tool calls, outputs, etc.)
            elif event.type == "run_item_stream_event":
                if hasattr(event, 'item'):
                    if event.item.type == "tool_call_item":
                        # Tool call started
                        tool_name = getattr(event, 'name', 'unknown')
                        if tool_name and tool_name in tool_status_messages:
                            current_tool = tool_name
                            status_msg.content = tool_status_messages[tool_name]
                            await status_msg.update()
                    elif event.item.type == "tool_call_output_item":
                        # Tool call completed - update status
                        if current_tool:
                            status_msg.content = f"✅ Completed {current_tool.replace('_', ' ').title()}... Generating next section..."
                            await status_msg.update()
                    elif event.item.type == "message_output_item":
                        # Handle message output items
                        try:
                            from agents import ItemHelpers
                            message_content = ItemHelpers.text_message_output(event.item)
                            # Add to final response content for later use
                            final_response_content += message_content
                            await status_msg.stream_token(message_content)
                        except:
                            # Fallback if ItemHelpers is not available or fails
                            pass

        # At this point, we have the complete response in final_response_content
        # Remove the status message and send the final response as a new message
        await status_msg.remove()  # Remove the status message

        # Send the final response as a new message
        if final_response_content.strip():
            final_msg = cl.Message(content=final_response_content)
            await final_msg.send()
        else:
            # If somehow we don't have content from streaming, use the status message content
            await status_msg.update()

        # Check if response contains a business plan (indicating generation phase)
        if "# Business Plan:" in final_response_content:
            # We have a complete business plan, reset session
            import uuid
            session_id = f"conversation_{uuid.uuid4().hex[:8]}"
            session = SQLiteSession(session_id)  # Create a new session for next conversation
            cl.user_session.set("session", session)
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
    session = cl.user_session.get("session")
    if session:
        # Optionally clear the session data
        pass
    cl.user_session.set("session", None)
    cl.user_session.set("startup_info", None)
    print("Chat ended")


if __name__ == "__main__":
    # Run: chainlit run main.py
    pass