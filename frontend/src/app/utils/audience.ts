import axios from "axios";

import type { FactionType } from "../types/factions";

/** The comma-separated names typed in a form, trimmed, without blanks. */
export function splitNames(text: string): string[] {
    return text
        .split(",")
        .map((name) => name.trim())
        .filter(Boolean);
}

/**
 * The ids behind the names typed for a private offer (users, factions). The
 * API wants ids, people know names. Throws an Error with a readable message
 * for a name nobody has; an empty list gives null, which means "everybody".
 */
export async function resolveAudience(
    userText: string,
    factionText: string,
    factions: FactionType[] | null,
): Promise<{ userIds: number[] | null; factionIds: number[] | null }> {
    const userIds: number[] = [];
    for (const name of splitNames(userText)) {
        try {
            const res = await axios.get<{ user_id: number }>(
                `/users/from_name/${encodeURIComponent(name)}`,
            );
            userIds.push(res.data.user_id);
        } catch (error: unknown) {
            if (axios.isAxiosError(error) && error.response?.status === 404) {
                throw new Error(`Utilisateur inconnu : ${name}`, {
                    cause: error,
                });
            }
            throw error;
        }
    }

    const factionIds = splitNames(factionText).map((name) => {
        const found = factions?.find(
            (f) => f.name.toLowerCase() === name.toLowerCase(),
        );
        if (!found) throw new Error(`Faction inconnue : ${name}`);
        return found.faction_id;
    });

    return {
        userIds: userIds.length ? userIds : null,
        factionIds: factionIds.length ? factionIds : null,
    };
}

/** The names of users, in order, as a comma-separated text (for a form). */
export async function userNamesText(ids: number[] | null): Promise<string> {
    const names = await Promise.all(
        (ids ?? []).map(async (id) => {
            try {
                const res = await axios.get<{ username: string }>(
                    `/users/detail/${id}`,
                );
                return res.data.username;
            } catch {
                return String(id);
            }
        }),
    );
    return names.join(", ");
}

/** The names of factions, as a comma-separated text (for a form). */
export function factionNamesText(
    ids: number[] | null,
    factions: FactionType[] | null,
): string {
    return (ids ?? [])
        .map(
            (id) =>
                factions?.find((f) => f.faction_id === id)?.name ?? String(id),
        )
        .join(", ");
}
