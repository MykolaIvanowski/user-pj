from app.events.producer import publish_event

async def dispatch_event(event_type: str, payload: dict):
    await publish_event(event_type, payload)
