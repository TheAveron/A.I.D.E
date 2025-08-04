import logo from "../../assets/images/CC_logo.png";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import * as Yup from "yup";
import { yupResolver } from "@hookform/resolvers/yup";
import { useAuth } from "../utils/authprovider";
import axios from "axios";

import "../../assets/css/pages/login.css";

type userDataLogin = {
    username: string;
    password: string;
};

const formSchema = Yup.object().shape({
    username: Yup.string().required("Username is required"),
    password: Yup.string().required("Password is required"),
});

function Login() {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<userDataLogin>({
        resolver: yupResolver(formSchema),
    });

    const { token, setToken } = useAuth() ?? {};
    const navigate = useNavigate();

    if (token) {
        return navigate("/A.I.D.E");
    }

    const onSubmit = handleSubmit(async (data) => {
        try {
            const response = await axios.post(
                "http://127.0.0.1:8000/auth/login",
                data
            );
            if (response.data && response.data.access_token) {
                setToken?.(response.data.access_token);
                axios.defaults.headers.common[
                    "Authorization"
                ] = `Bearer ${token}`;
                console.log("You Are Successfully Logged In");
                navigate("/A.I.D.E");
            } else {
                console.log("Login failed: No token received");
            }
        } catch (error: any) {
            if (error.response?.status === 401) {
                console.log("Password is incorrect");
            } else if (error.response?.status === 404) {
                console.log("You don't have an account with this username");
            } else {
                console.log("Login error:", error.message);
            }
        }
    });

    return (
        <>
            <div className="content">
                <section id="login">
                    <form className="App" onSubmit={onSubmit}>
                        <div className="imgcontainer">
                            <img
                                src={logo}
                                style={{
                                    maxWidth: "20vw",
                                    maxHeight: "20vh",
                                    borderRadius: "100%",
                                }}
                                alt="Avatar"
                                className="avatar"
                            />
                        </div>
                        <div className="container">
                            <label>
                                <b>Nom d'utilisateur</b>
                            </label>
                            <input
                                type="username"
                                {...register("username", { required: true })}
                                placeholder="Entrer votre nom"
                            />
                            {errors.username && (
                                <span style={{ color: "red" }}>
                                    *Nom* obligatoire
                                </span>
                            )}
                            <label>
                                <b>Mot de passe</b>
                            </label>
                            <input
                                type="password"
                                {...register("password", { required: true })}
                                placeholder="Entrez votre mot de passe"
                            />
                            {errors.password && (
                                <span style={{ color: "red" }}>
                                    *Mot de passe* obligatoire
                                </span>
                            )}

                            <div className="form-end">
                                <input
                                    type="submit"
                                    className="button"
                                    value="Log in"
                                />
                                <Link to="../register">Pas de compte ?</Link>
                            </div>
                        </div>
                    </form>
                </section>
            </div>
        </>
    );
}

export default Login;
