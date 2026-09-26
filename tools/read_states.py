"""Print the current state of every entity. Usage: python tools/read_states.py"""
import asyncio

from device import connect


async def main():
    cli = await connect()
    entities, _ = await cli.list_entities_services()
    names = {e.key: e.name for e in entities}
    states = {}

    def on_state(st):
        if st.key in names and hasattr(st, "state"):
            states[names[st.key]] = st.state

    cli.subscribe_states(on_state)
    await asyncio.sleep(3)
    for name in sorted(states):
        print(f"{name}: {states[name]}")
    await cli.disconnect()


asyncio.run(main())
