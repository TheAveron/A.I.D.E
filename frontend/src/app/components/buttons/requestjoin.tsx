import { useJoinRequestActions, useMyJoinRequest } from "../hooks/joinrequests";

/**
 * For a faction that takes members on request only: ask to join it, or
 * withdraw the request already made. A user has one open request at a time.
 */
export function RequestJoinButton({
    factionId,
    onChanged,
}: {
    factionId: number;
    onChanged?: () => void;
}) {
    const { request, loading: loadingRequest, refresh } = useMyJoinRequest();
    const { create, withdraw, loading, error } = useJoinRequestActions();

    const done = () => {
        refresh();
        onChanged?.();
    };

    if (loadingRequest) return null;

    if (request && request.faction_id === factionId) {
        return (
            <>
                <span>Demande en attente</span>{" "}
                <button
                    type="button"
                    className="button"
                    disabled={loading}
                    onClick={async () => {
                        if (await withdraw(request.request_id)) done();
                    }}
                >
                    Retirer
                </button>
                {error && <p role="alert">{error}</p>}
            </>
        );
    }

    return (
        <>
            <button
                type="button"
                className="button"
                disabled={loading || request !== null}
                title={
                    request
                        ? "Vous avez déjà une demande en attente dans une autre faction"
                        : undefined
                }
                onClick={async () => {
                    if (await create(factionId)) done();
                }}
            >
                Demander à rejoindre
            </button>
            {error && <p role="alert">{error}</p>}
        </>
    );
}
