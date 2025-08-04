import Profile from "../components/profile";
import FactionList from "../components/factionlist";
import { useUser } from "../components/hooks/user";
import { useParams } from "react-router-dom";

import "../../assets/css/components/container.css";
import "../../assets/css/components/snippets.css";

function UserPage() {
    const { userid } = useParams();

    if (!userid) {
        return <p style={{ color: "red" }}>No user id found.</p>;
    }

    const { user, loading } = useUser(userid);

    if (loading) {
        return (
            <div className="profile-container">
                <p>Chargement...</p>
            </div>
        );
    }

    if (!user) {
        return <p style={{ color: "red" }}>No user data found.</p>;
    }

    return (
        <div className="information-container">
            <Profile value={user} />

            <FactionList />
        </div>
    );
}

export default UserPage;
