import { useMe } from "../components/hooks/me";

import Profile from "../components/profile";
import FactionList from "../components/factionlist";

import "../../assets/css/components/container.css";
import "../../assets/css/components/snippets.css";

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
            <FactionList />
        </div>
    );
}

export default UserPage;
