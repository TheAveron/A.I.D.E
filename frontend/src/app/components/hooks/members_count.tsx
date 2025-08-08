import axios from "axios";
import type { UserType } from "../../types/users"; // adjust path as needed

export async function fetchMembersCount(factionId: string): Promise<number> {
    try {
        const res = await axios.get<UserType[]>(
            `http://127.0.0.1:8000/users/faction/${factionId}`
        );
        return res.data.length;
    } catch (error) {
        console.error(
            `Error fetching members for faction ${factionId}:`,
            error
        );
        return 0;
    }
}
