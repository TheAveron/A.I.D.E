import interactions
from .get_data import *
from operator import itemgetter


class Players(interactions.Extension):

  def __init__(self, client) -> None:
    self.client = client

  @interactions.slash_command(
    name="inscription",
    description=
    "Vous enregistre dans la liste des joueurs classés au FriendShip Credit",
    scopes=[784712879831646208])
  async def register(self, ctx: interactions.SlashContext):
    users = get_users_data()

    embed = interactions.Embed(title="Register")
    if not str(ctx.author_id) in users:
      users[str(ctx.author_id)] = 0

      publish_users_data(users)

      embed.description = "Vous avez bien été enregistré !"
    else:
      embed.description = "Vous ne pouvez pas effectuer la commande, vous faites déjà partie de la liste."

    await ctx.send(embeds=embed)

  @interactions.slash_command(
    name="points",
    description="Vous donne votre nombre de FriendShip Credit",
    scopes=[784712879831646208])
  async def points(self, ctx: interactions.SlashContext):
    users = get_users_data()

    embed = interactions.Embed(title="Crédits")

    if str(ctx.author_id) in users:
      point = users[str(ctx.author_id)]

      embed.description = f"FriendShip Credit: {point} points"
    else:
      embed.description = "Vous ne pouvez pas effectuer la commande, vous devez être enregistré avant !"

    await ctx.send(embeds=embed)

  @interactions.slash_command(name="add_score",
                              description="Donne des FriendShip Credit",
                              scopes=[784712879831646208])
  @interactions.check(interactions.is_owner())
  @interactions.slash_option(name="points",
                             description="Points à ajouter",
                             required=True,
                             opt_type=interactions.OptionType.INTEGER)
  @interactions.slash_option(
    name="user",
    description="L'utilisateur auquel ajouter des points",
    required=True,
    opt_type=interactions.OptionType.USER)
  async def add(self, ctx: interactions.SlashContext, user, points):
    users = get_users_data()
    embed = interactions.Embed(title="Ajout de points")

    if str(user.id) in users:
      users[str(user.id)] += points

      publish_users_data(users)

      embed.description = f" {users[str(user.id)]} points on étés attribués à {user}"
    else:
      embed.description = "Vous ne pouvez pas effectuer la commande, l'utilisateur doit être enregistré avant !"
    await ctx.send(embeds=embed)

  @interactions.slash_command(name="sub_score",
                              description="Enlève des FriendShip Credit",
                              scopes=[784712879831646208])
  @interactions.check(interactions.is_owner())
  @interactions.slash_option(name="points",
                             description="Points à enlever",
                             required=True,
                             opt_type=interactions.OptionType.INTEGER)
  @interactions.slash_option(
    name="user",
    description="L'utilisateur auquel enlever des points",
    required=True,
    opt_type=interactions.OptionType.USER)
  async def sub(self, ctx: interactions.SlashContext, user, points):
    users = get_users_data()
    embed = interactions.Embed(title="Retranchement de points")

    if str(user.id) in users:
      users[str(user.id)] -= points

      publish_users_data(users)

      embed.description = f" {users[str(user.id)]} points on étés retirés à {user}"
    else:
      embed.description = "Vous ne pouvez pas effectuer la commande, l'utilisateur doit être enregistré avant !"
    await ctx.send(embeds=embed)

  @interactions.slash_command(
    name="liste",
    description="Liste des inscrits au FriendShip Credit",
    scopes=[784712879831646208])
  async def inscription(self, ctx: interactions.SlashContext):
    users = get_users_data()
    embed = interactions.Embed(title="Liste des inscrits", description="")

    users_bis = [(user, users[user]) for user in users]

    users_bis.sort(key=itemgetter(1), reverse=True)

    for user in users_bis:
      embed.description += f"<@{user[0]}> : {user[1]} points\n"

    await ctx.send(embeds=embed)


def setup(client):
  Players(client)
