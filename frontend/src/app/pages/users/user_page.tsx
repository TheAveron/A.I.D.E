import { useParams } from "react-router";

import { useUser } from "../../hooks/users/user";
import { useMe } from "../../hooks/users/me";

import Profile from "../../components/users/profile";
import OfferList from "../../components/offers/offerslist";
import TransactionsTable from "../../components/transactions/transaction_table";

function UserPage() {
    // /user/:userid - the page of the user in the URL (it used to always show
    // the logged-in user's own page, whoever's name was clicked).
    const { userid } = useParams();
    const { user, loading, error } = useUser(userid ?? null);
    const { user: me } = useMe();

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
                    <TransactionsTable
                        userId={user.user_id.toString()}
                        hideWhenEmpty={me?.user_id !== user.user_id}
                    />
                    <OfferList
                        userId={user.user_id.toString()}
                        canCreate={me?.user_id === user.user_id}
                    />
                </>
            )}
        </div>
    );
}

export default UserPage;
