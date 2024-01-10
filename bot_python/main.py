import interactions
import os

from Utilities.checks import Is_Owner
from keepalive import keep_alive

token = os.environ['TOKEN']

bot = interactions.Client(token=token, owner_ids=[762729436268593183])
bot.load_extension("Commands.users")

@interactions.slash_command(
	name="stop_bot",
  	description="Stop the bot",
	  dm_permission=True
)
@interactions.check(Is_Owner)
async def stopbot(ctx:interactions.SlashContext):
  await ctx.send('Bot stopped !')
  await ctx.bot.stop()

@interactions.listen(event_name="Ready")
async def on_ready(event: interactions.api.events.Ready):
	"""Envoie ready quand le bot est lancé"""
	print("Ready !")

keep_alive()
bot.start()
