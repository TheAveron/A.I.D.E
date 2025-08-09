import { useMe } from "../components/hooks/me";

import Profile from "../components/profile";
import OfferList from "../components/offerslist";
import TransactionsTable from "../components/snippets/transaction_table";

function ProfileComponent() {
    const { user, loading, error } = useMe();

    return !error ? (
        !loading ? (
            user ? (
                <div className="information-container user-page">
                    <Profile value={user} />

                    <TransactionsTable userId={user?.user_id.toString()} />
                    <OfferList userId={user.user_id.toString()} />
                </div>
            ) : (
                <div
                    style={{
                        textAlign: "center",
                        placeContent: "center",
                        placeItems: "center",
                        color: "red",
                        fontSize: "3em",
                        margin: "auto",
                        height: "calc(100vh - var(--header-height))",
                    }}
                >
                    Error: No profile data found.
                </div>
            )
        ) : (
            <div className="profile-container">
                <p>Chargement...</p>
            </div>
        )
    ) : (
        <div className="profile-container">
            <p>{error}</p>
        </div>
    );
}

export default ProfileComponent;
