import interactions
from .get_data import * 

async def Is_Registered(ctx:interactions.SlashContext=None,user: interactions.User | int=None, title:str=None)-> bool:
	embed=interactions.Embed(title=title, description="Vous n'êtes pas encore enregistré ! Vous ne pouvez pas effectuer cette commande !")
	
	if title==None:
		embed.title= ctx._command_name

	if user==None:
		if get_user(ctx.author_id)==None:
			await ctx.send(embed=embed)
			return False
		return True

	if type(user)==int:
		user_points=get_user(user)
	else:
		user_points=get_user(user.id)

	if user_points==None:
		
		embed.description="L'utilisateur n'est pas encore enregistré ! Vous ne pouvez pas modifier ou afficher ses points !"

		await ctx.send(embed=embed)
		return False

	return True

async def Is_Not_Registered(ctx:interactions.SlashContext=None,user: interactions.User | int=None, title:str=None)->bool:
	embed=interactions.Embed(title=title, description="Vous êtes déjà enregistré ! Vous ne pouvez pas effectuer cette commande !")
	
	if title==None:
		embed.title=ctx._command_name

	if user==None:
		if not get_user(ctx.author_id)==None:
			await ctx.send(embed=embed)
			return False
		return True

	if type(user)==int:
		user_points=get_user(user)
	else:
		user_points=get_user(user.id)

	if not user_points==None:
		
		embed.description="L'utilisateur est déjà enregistré ! Vous ne pouvez pas l'enregistrer à nouveau !"

		await ctx.send(embed=embed)
		return False

	return True


async def Is_Owner(ctx:interactions.SlashContext)->bool:
	return ctx.author_id in ctx.bot.owner_ids
	
