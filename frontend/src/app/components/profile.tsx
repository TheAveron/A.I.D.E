import axios from "axios";
import type { UserProfile } from "../types/users";
import type { FactionInfo } from "../types/factions";
import { useEffect, useState } from "react";
import "../../assets/css/components/profile.css";

function Profile({ value }: { value: UserProfile }) {
    const profile = value;
    const [faction, setFaction] = useState<FactionInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<String | null>(null);

    if (profile.faction_id) {
        useEffect(() => {
            const fetchFaction = async () => {
                try {
                    const res = await axios.get<FactionInfo>(
                        "http://127.0.0.1:8000/faction/" + profile.faction_id
                    );
                    setFaction(res.data);
                } catch (err) {
                    setError("Failed to load Faction infos.");
                } finally {
                    setLoading(false);
                }
            };

            fetchFaction();
        }, []);

        if (loading) {
            return <p>Loading...</p>;
        }

        if (error) {
            return <p style={{ color: "red" }}>Error: {error}</p>;
        }
    }

    return (
        <>
            <div className="profile-header">
                <div className="profile-username">{profile.username}</div>
                {profile.is_admin && (
                    <div className="profile-role">Administrateur</div>
                )}
            </div>

            <div className="profile-info">
                <div className="profile-info-row">
                    <span className="profile-info-label">Faction:</span>
                    <span className="profile-info-value">
                        {faction?.name ?? "Aucune"}
                    </span>
                </div>
                <div className="profile-info-row">
                    <span className="profile-info-label">Email:</span>
                    <span className="profile-info-value">
                        {profile.email ?? "Not provided"}
                    </span>
                </div>
                <div className="profile-info-row">
                    <span className="profile-info-label">Inscription:</span>
                    <span className="profile-info-value">
                        {new Date(profile.created_at).toLocaleDateString()}
                    </span>
                </div>
            </div>
        </>
    );
}

export default Profile;
