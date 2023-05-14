import interactions
import json

with open("configuration.json",'r',encoding='utf8') as config:
    data = json.load(config)
    token=data['token']
    owner=data['owner']

bot=interactions.Client(token=token)
bot.load_extension("Commands.new_users")

@interactions.slash_command(
	name="stop",
	description="Stop the bot",
	scopes=[784712879831646208],
)
@interactions.check(
	interactions.is_owner()
)
async def stop(ctx):
	await ctx.send('Bot stopped !')
	await bot.stop()

bot.start()