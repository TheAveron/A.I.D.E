from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_seed_data():
    admin_password = get_password_hash("admin_password")
    player_password = get_password_hash("player_password")

    return [("admin", admin_password, True), ("player1", player_password, False)]
