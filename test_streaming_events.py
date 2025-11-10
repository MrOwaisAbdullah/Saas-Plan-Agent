import asyncio
import random
from agents import Agent, ItemHelpers, Runner, function_tool
from client import model


@function_tool
def how_many_jokes() -> int:
    """Return a random integer of jokes to tell between 1 and 10 (inclusive)."""
    return random.randint(1, 10)


async def main():
    agent = Agent(
        name="Joker",
        instructions="First call the `how_many_jokes` tool, then tell that many jokes.",
        tools=[how_many_jokes],
        model=model
    )

    result = Runner.run_streamed(
        agent,
        input="Hello",
    )
    print("=== Run starting ===")
    # print(f"Streaming output:\n {result}")
    async for event in result.stream_events():
        # We'll ignore the raw responses event deltas
        if event.type == "raw_response_event":
            continue
        elif event.type == "agent_updated_stream_event":
            print(f"Agent updated: {event.new_agent.name}")
            continue
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print("-- Tool was called")
            elif event.item.type == "tool_call_output_item":
                print(f"-- Tool output: {event.item.output}")
            elif event.item.type == "message_output_item":
                print(f"-- Message output:\n {ItemHelpers.text_message_output(event.item)}")
            else:
                print(f"-- Other item type: {event.item.type}")
        else:
            print(f"Event type: {event.type}")

    print("=== Run complete ===")


if __name__ == "__main__":
    asyncio.run(main())