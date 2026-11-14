import { useMemberCounts } from "../hooks/member_counts";
import { useMembership } from "../hooks/membership";

/** Remove a member from one's faction; `onKicked` reloads the member list. */
export function KickMemberButton({
    userId,
    username,
    onKicked,
}: {
    userId: number;
    username: string;
    onKicked: () => void;
}) {
    const { kick, loading, error } = useMembership();
    const { refresh: refreshCounts } = useMemberCounts();

    const onClick = async () => {
        if (!window.confirm(`Exclure ${username} de la faction ?`)) return;
        if (await kick(userId)) {
            onKicked();
            refreshCounts();
        }
    };

    return (
        <>
            <button
                type="button"
                className="button"
                disabled={loading}
                onClick={onClick}
            >
                Exclure
            </button>
            {error && <p role="alert">{error}</p>}
        </>
    );
}
