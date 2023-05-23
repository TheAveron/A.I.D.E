import json

def get_users_data() -> dict[str,int]:
	with open("Static/users.json","r", encoding='utf8') as datas:
		users=json.load(datas)
	return users

def get_user(user:int):
	users=get_users_data()
	try:
		return users[str(user)]
	except KeyError:
		return None

def publish_users_data(users:dict[str,int])-> None:
	with open("Static/users.json",'w',encoding='utf8') as datas:
		json.dump(users, datas, indent=4)


def publish_user(user:tuple[int,int])-> None:
	users = get_users_data()
	users[str(user[0])] = user[1]
	publish_users_data(users)