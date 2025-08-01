import { useEffect, useState } from "react";
import axios from "axios";

function Profile() {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios
            .get("http://127.0.0.1:8000/users/me")
            .then((res) => {
                setProfile(res.data);
                setLoading(false);
            })
            .catch((err) => {
                setError(err.message);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return <p>Loading...</p>;
    }

    if (error) {
        return <p style={{ color: "red" }}>Error: {error}</p>;
    }

    if (!profile) {
        return <p>No profile data found.</p>;
    }

    return (
        <div>
            <h2>Profile</h2>
            <pre>{JSON.stringify(profile, null, 2)}</pre>
        </div>
    );
}

export default Profile;
