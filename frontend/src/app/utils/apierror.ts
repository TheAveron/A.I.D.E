import axios from "axios";

/**
 * The human-readable part of an API error body.
 *
 * FastAPI answers `{"detail": "text"}` for errors raised by the application,
 * but `{"detail": [{"loc": ..., "msg": "text", ...}, ...]}` for validation
 * errors (422). Showing the second form as is gives "[object Object]".
 */
export function getErrorDetail(data: unknown): string | null {
    if (!data || typeof data !== "object" || !("detail" in data)) return null;

    const { detail } = data as { detail: unknown };

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
        const messages = detail
            .map((issue: unknown) =>
                issue &&
                typeof issue === "object" &&
                "msg" in issue &&
                typeof issue.msg === "string"
                    ? // pydantic prefixes the messages of custom checks
                      issue.msg.replace(/^Value error, /, "")
                    : null,
            )
            .filter((message): message is string => message !== null);

        return messages.length > 0 ? messages.join(", ") : null;
    }

    return null;
}

/** A message for any error thrown by an axios call. */
export function getErrorMessage(
    error: unknown,
    fallback = "Erreur inconnue",
): string {
    if (axios.isAxiosError(error)) {
        if (!error.response) return "Impossible de joindre le serveur";

        return getErrorDetail(error.response.data) ?? error.message ?? fallback;
    }

    return error instanceof Error ? error.message : fallback;
}
