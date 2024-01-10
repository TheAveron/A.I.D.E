import interactions

class CustomClient(interactions.Client):
    @interactions.listen(disable_default_listeners=True)  # tell the dispatcher that this replaces the default listener
    async def on_command_error(self, event: interactions.api.events.CommandError):
        interactions.logger.error(event.error)
        if not event.ctx.responded:
            await event.ctx.send("Something went wrong.")