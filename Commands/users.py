import interactions
from .get_data import *


class Players(interactions.Extension):

  def __init__(self, client) -> None:
    self.client = client

  @interactions.slash_command(
    name="register",
    description=
    "Vous enregistre dans la liste des joueurs classés au FriendShip Credit",
    scopes=[784712879831646208])
  async def register(self, ctx: interactions.SlashContext):
    users = get_users_data()

    if not str(ctx.author_id) in users:
      users[str(ctx.author_id)] = 0

      publish_users_data(users)

      await ctx.send("Vous avez été enregistré !")
    else:
      await ctx.send(
        "Vous ne pouvez pas effectuer la commande, vous faites déjà partie de la liste"
      )

  @interactions.slash_command(
    name="points",
    description="Vous donne votre nombre de FriendShip Credit",
    scopes=[784712879831646208])
  async def points(self, ctx: interactions.SlashContext):
    users = get_users_data()

    if str(ctx.author_id) in users:
      point = users[str(ctx.author_id)]

      await ctx.send(f"Vous avez {point} points")
    else:
      await ctx.send(
        "Vous ne pouvez pas effectuer la commande, vous devez être enregistré avant !"
      )

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

    if str(user.id) in users:
      users[str(user.id)] += points

      publish_users_data(users)

      await ctx.send(f"Vous avez ajouté {users[str(user.id)]} points à {user}")
    else:
      await ctx.send(
        "Vous ne pouvez pas effectuer la commande, l'utilisateur doit être enregistré avant !"
      )

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

    if str(user.id) in users:
      users[str(user.id)] -= points

      publish_users_data(users)

      await ctx.send(f"Vous avez enlevé {users[str(user.id)]} points à {user}")
    else:
      await ctx.send(
        "Vous ne pouvez pas effectuer la commande, l'utilisateur doit être enregistré avant !"
      )


def setup(client):
  Players(client)
