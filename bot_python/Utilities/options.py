import interactions

def User_option():
	"""Call with `@User_option()`
	
	Set a required option for user input"""

	def wrapper(func):
		return interactions.slash_option(
			name="user",
			description="L'utilisateur cible",
			opt_type=interactions.OptionType.USER,
			required=True
		)(func)

	return wrapper
	
def Point_option():
	"""Call with `@Point_option()`
	
	Set a required option for points input"""
	
	def wrapper(func):
		return interactions.slash_option(
			name="points",
			description="Points à modifier",
			opt_type=interactions.OptionType.INTEGER,
			required=True
		)(func)

	return wrapper