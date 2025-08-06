import Profile from "../components/profile";
import FactionList from "../components/factionlist";

import { useMe } from "../components/hooks/me";

import "../../assets/css/components/container.css";
import "../../assets/css/components/snippets.css";

function ProfileComponent() {
    const { user, loading, error } = useMe();

    return !error ? (
        !loading ? (
            user ? (
                <div className="information-container">
                    <Profile value={user} />
                    <FactionList />{" "}
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
