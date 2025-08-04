import { useEffect, useState } from "react";
import axios from "axios";
import type { UserType } from "../types/users";
import Profile from "../components/profile";
import FactionList from "../components/factionlist";
import { useAuth } from "../utils/authprovider";

import "../../assets/css/components/container.css";
import "../../assets/css/components/snippets.css";

function ProfileComponent() {
    const { token } = useAuth() ?? {};
    const [profile, setProfile] = useState<UserType | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<String | null>(null);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const res = await axios.get<UserType>(
                    "http://127.0.0.1:8000/users/me",
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                setProfile(res.data);
            } catch (err) {
                setError("Failed to load profile.");
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, []);

    if (loading) {
        return (
            <div className="profile-container">
                <p>Chargement...</p>
            </div>
        );
    }

    if (error) {
        return <p style={{ color: "red" }}>Error: {error}</p>;
    }

    if (!profile) {
        return <p style={{ color: "red" }}>No profile data found.</p>;
    }

    return (
        <div className="information-container">
            <Profile value={profile} />
            <FactionList />
        </div>
    );
}

export default ProfileComponent;
