/** The value of a datetime-local input (local time) for an ISO date. */
export function toLocalInput(iso: string | null): string {
    if (!iso) return "";
    const date = new Date(iso);
    const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return shifted.toISOString().slice(0, 16);
}

/**
 * The ISO date for what a datetime-local input holds; null when empty.
 * Throws an Error with a readable message for a date the server would refuse.
 */
export function fromLocalInput(value: string): string | null {
    if (!value.trim()) return null;
    const date = new Date(value);
    if (Number.isNaN(date.getTime()))
        throw new Error("Date d'expiration invalide");
    const now = Date.now();
    if (date.getTime() <= now) {
        throw new Error("La date d'expiration doit être dans le futur");
    }
    if (date.getTime() - now > 366 * 24 * 3600 * 1000) {
        throw new Error("L'expiration ne peut pas dépasser un an");
    }
    return date.toISOString();
}

export function formatExpiry(iso: string): string {
    return new Date(iso).toLocaleString("fr-FR", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    });
}
