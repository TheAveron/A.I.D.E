import { useMe } from "../../hooks/users/me";

import Profile from "../../components/users/profile";
import OfferList from "../../components/offers/offerslist";
import { LeaveFactionButton } from "../../components/factions/leavefaction";
import ChangePassword from "../../components/users/change_password";
import PreferencesPanel from "../../components/users/preferences_panel";
import TransactionsTable from "../../components/transactions/transaction_table";

function ProfileComponent() {
    const { user, loading, error } = useMe();

    return !error ? (
        !loading ? (
            user ? (
                <div className="information-container user-page">
                    <Profile value={user} />
                    <LeaveFactionButton />
                    <PreferencesPanel />
                    <ChangePassword />

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
                    Profil introuvable.
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
