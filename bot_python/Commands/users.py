import interactions
from operator import itemgetter

from Utilities.checks import Is_Not_Registered, Is_Registered, Is_Owner
from Utilities.options import User_option, Point_option
from Utilities.get_data import get_user, publish_user, get_users_data

class Players(interactions.Extension):
	def __init__(self, client) -> None:
		self.client = client

	@interactions.slash_command(
		name="inscription",
		description="Vous enregistre dans la liste des joueurs classés au FriendShip Credit",
		scopes=[784712879831646208]
	)
	@interactions.check(Is_Not_Registered)
	async def register(self, ctx: interactions.SlashContext):
		embed = interactions.Embed(title="Register")
		
		publish_user((ctx.author_id, 0))
		embed.description = "Vous avez bien été enregistré !"
		return await ctx.send(embeds=embed)

	@interactions.slash_command(
		name="points",
		description="Vous donne votre nombre de FriendShip Credit",
		scopes=[784712879831646208]
	)
	
	@interactions.check(Is_Registered)
	async def points(self, ctx: interactions.SlashContext):
		points = get_user(ctx.author_id)
		embed = interactions.Embed(title="Crédits", description = f"FriendShip Credit: {points} points")
		return await ctx.send(embeds=embed)

	@interactions.slash_command(
		name="add_score",
		description="Donne des FriendShip Credit",
		scopes=[784712879831646208]
	)
	@interactions.check(Is_Owner)
	@Point_option()
	@User_option()
	async def add(self, ctx: interactions.SlashContext, user:interactions.User, points:int):
		"""Commande pour ajouter des points à un utilisateur"""		
		if await Is_Registered(ctx, user):
			user_points = get_user(int(user.id)) + points
			
			publish_user((user.id, user_points))
			embed = interactions.Embed(title="Retrait de points",description = f"{points} points on étés ajoutés à {user}")
			
			return await ctx.send(embeds=embed)

	@interactions.slash_command(
		name="sub_score",
		description="Enlève des FriendShip Credit",
		scopes=[784712879831646208],
	)
	@interactions.check(Is_Owner)
	@Point_option()
	@User_option()
	async def sub(self, ctx: interactions.SlashContext, user:interactions.User, points):
		"""Commande pour retirer des points à un utilisateur"""
		if await Is_Registered(ctx, user):
			user_points = get_user(int(user.id)) - points
			
			publish_user((user.id, user_points))
			embed = interactions.Embed(title="Retrait de points",description = f"{points} points on étés retirés à {user}")
			
			return await ctx.send(embeds=embed)

	@interactions.slash_command(
		name="liste",
		description="Liste des inscrits au FriendShip Credit",
		scopes=[784712879831646208]
	)
	async def inscription(self, ctx: interactions.SlashContext):
		users = get_users_data()
		embed = interactions.Embed(title="Liste des inscrits", description="")

		users_bis = [(user, users[user]) for user in users]
		users_bis.sort(key=itemgetter(1), reverse=True)

		for user in users_bis:
			embed.description += f"<@{user[0]}> : {user[1]} points\n"

		return await ctx.send(embeds=embed)


def setup(client):
	Players(client)
