import json

def get_users_data():
	with open("Static/users.json","r", encoding='utf8') as datas:
		users=json.load(datas)
	return users

def publish_users_data(users):
	with open("Static/users.json",'w',encoding='utf8') as datas:
		json.dump(users, datas, indent=4)