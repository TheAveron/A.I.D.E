import { useEffect, useState } from "react";
import axios from "axios";
import "../../assets/css/components/profile.css";
import type { UserProfile } from "../types/users";
import Profile from "../components/profile";
import FactionList from "../components/factionlist";

function ProfileComponent() {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<String | null>(null);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const res = await axios.get<UserProfile>(
                    "http://127.0.0.1:8000/users/me"
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
                <p>Loading...</p>
            </div>
        );
    }

    if (error) {
        return <p style={{ color: "red" }}>Error: {error}</p>;
    }

    if (!profile) {
        return <p>No profile data found.</p>;
    }

    return (
        <div className="profile-container">
            <div className="profile-snippet">
                <Profile value={profile} />
            </div>
            <div className="faction-snippet">
                <FactionList />
            </div>
        </div>
    );
}

export default ProfileComponent;
