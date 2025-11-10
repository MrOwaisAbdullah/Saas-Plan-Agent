import asyncio
from agents import Agent, ItemHelpers, Runner, function_tool
from custom_agents import business_plan_generator_agent
from search_tools import tavily_search_tool


async def explore_all_events():
    """Explore all possible streaming events from the business plan generator"""
    
    # Create a simple test input
    test_input = """
    Current startup information gathered:
    - Name: Test Startup
    - Idea: An AI-powered productivity tool
    - Target Market: Small to medium businesses
    - Key Features: Task automation, analytics dashboard, team collaboration
    
    Latest user message: Please generate a complete business plan.
    
    Your task:
    1. Generate the complete business plan since all information is available.
    """
    
    print("=== Starting business plan generation with full event capture ===")
    result = Runner.run_streamed(
        business_plan_generator_agent,
        test_input
    )
    
    event_count = 0
    async for event in result.stream_events():
        event_count += 1
        print(f"\n--- Event {event_count} ---")
        print(f"Event Type: {event.type}")
        
        if hasattr(event, 'data'):
            print(f"Event Data Type: {type(event.data)}")
            # Try to print some attributes without causing errors
            try:
                if hasattr(event.data, '__dict__'):
                    for attr in dir(event.data):
                        if not attr.startswith('_'):
                            val = getattr(event.data, attr)
                            if not callable(val):
                                print(f"  {attr}: {val}")
            except:
                print("  (Could not display data attributes)")
        
        if hasattr(event, 'item'):
            print(f"Item Type: {event.item.type}")
            if event.item.type == "tool_call_item":
                print("-- Tool was called")
                if hasattr(event.item, 'tool_call'):
                    print(f"  Tool name: {event.item.tool_call.name}")
                    print(f"  Tool arguments: {event.item.tool_call.arguments}")
            elif event.item.type == "tool_call_output_item":
                print(f"-- Tool output received")
                if hasattr(event.item, 'output'):
                    print(f"  Output preview: {str(event.item.output)[:100]}...")
            elif event.item.type == "message_output_item":
                print(f"-- Message output")
                try:
                    text_output = ItemHelpers.text_message_output(event.item)
                    print(f"  Message preview: {text_output[:100]}...")
                except Exception as e:
                    print(f"  Could not get text output: {e}")
        
        # Print the raw event for debugging
        print(f"Full event keys: {event.__dict__.keys() if hasattr(event, '__dict__') else 'No dict'}")
        
        if event_count > 20:  # Limit for testing
            print("\n--- Event capture stopped after 20 events for brevity ---")
            break
    
    print(f"\n=== Completed. Processed {event_count} events ===")


if __name__ == "__main__":
    asyncio.run(explore_all_events())