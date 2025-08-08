import { useUser } from "../hooks/user";

export default function Username({ userId }: { userId: string }) {
    const { user } = useUser(userId);

    return <span className="username">{user?.username}</span>;
}
