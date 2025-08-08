import { useMe } from "../components/hooks/me";

import Profile from "../components/profile";
import OfferList from "../components/offerslist";
import TransactionsTable from "../components/snippets/transaction_table";

function UserPage() {
    const { user, loading, error } = useMe();

    return (
        <div className="information-container">
            {!error ? (
                !loading ? (
                    user ? (
                        <Profile value={user} />
                    ) : (
                        <div className="profile-container">
                            <p>No user Found</p>
                        </div>
                    )
                ) : (
                    <div className="profile-container">
                        <p>{error}</p>
                    </div>
                )
            ) : (
                <div className="profile-container">
                    <p>{error}</p>
                </div>
            )}
            <TransactionsTable userId={user?.user_id.toString()} />
            <OfferList userId={user?.user_id.toString()} />
        </div>
    );
}

export default UserPage;
