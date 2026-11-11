import { useParams } from "react-router";

import { useUser } from "../components/hooks/user";

import Profile from "../components/profile";
import OfferList from "../components/offerslist";
import TransactionsTable from "../components/snippets/transaction_table";

function UserPage() {
    // /user/:userid - the page of the user in the URL (it used to always show
    // the logged-in user's own page, whoever's name was clicked).
    const { userid } = useParams();
    const { user, loading, error } = useUser(userid ?? null);

    return (
        <div className="information-container">
            {error ? (
                <div className="profile-container">
                    <p>{error}</p>
                </div>
            ) : loading ? (
                <div className="profile-container">
                    <p>Chargement...</p>
                </div>
            ) : user ? (
                <Profile value={user} />
            ) : (
                <div className="profile-container">
                    <p>Utilisateur introuvable</p>
                </div>
            )}
            {user && (
                <>
                    <TransactionsTable userId={user.user_id.toString()} />
                    <OfferList userId={user.user_id.toString()} />
                </>
            )}
        </div>
    );
}

export default UserPage;
