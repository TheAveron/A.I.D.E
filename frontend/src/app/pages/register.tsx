import { useForm } from "react-hook-form";
import logo from "../../assets/images/CC_logo.png";
import { Link, useNavigate } from "react-router-dom";
import { yupResolver } from "@hookform/resolvers/yup";
import * as Yup from "yup";
import axios from "axios";
import { useAuth } from "../utils/authprovider";

import "../../assets/css/pages/login.css";

type userDataRegistration = {
    username: string;
    password: string;
    cpassword: string;
};

const formSchema = Yup.object().shape({
    username: Yup.string().required("Username is required"),
    password: Yup.string()
        .required("Password is required")
        .min(4, "Password length should be at least 4 characters")
        .max(12, "Password cannot exceed more than 12 characters"),
    cpassword: Yup.string()
        .required("Confirm Password is required")
        .min(4, "Password length should be at least 4 characters")
        .max(12, "Password cannot exceed more than 12 characters")
        .oneOf([Yup.ref("password")], "Passwords do not match"),
});

function Register() {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<userDataRegistration>({
        resolver: yupResolver(formSchema),
    });

    const navigate = useNavigate();
    const { token, setToken } = useAuth() ?? {};
    if (token) {
        return navigate("/A.I.D.E");
    }

    const onSubmit = handleSubmit(async (data) => {
        try {
            const response = await axios.post(
                "http://127.0.0.1:8000/auth/register",
                {
                    username: data.username,
                    password: data.password,
                    is_admin: false,
                }
            );
            if (response.data && response.data.access_token) {
                setToken?.(response.data.access_token);
                axios.defaults.headers.common[
                    "Authorization"
                ] = `Bearer ${token}`;
                navigate("/A.I.D.E");
                console.log("Registration successful!");
            } else {
                console.log("Registration failed: No token received");
            }
        } catch (error: any) {
            if (error.response?.status === 409) {
                console.log("Username already exists");
            } else {
                console.log("Registration error:", error.message);
            }
        }
    });
    return (
        <>
            <div className="content">
                <section id="register">
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
                                placeholder="Entrez un nom"
                            />
                            {errors.username?.message && (
                                <span style={{ color: "red" }}>
                                    *Nom* obligatoire,
                                    {errors.username?.message}
                                </span>
                            )}
                            <label>
                                <b>Mot de passe</b>
                            </label>
                            <input
                                type="password"
                                {...register("password")}
                                placeholder="Entrez un mot de passe"
                            />
                            {errors.password && (
                                <span style={{ color: "red" }}>
                                    {errors.password?.message}
                                </span>
                            )}
                            <label>
                                <b>Confirmation</b>
                            </label>
                            <input
                                type="password"
                                {...register("cpassword")}
                                placeholder="Entrez votre mot de passe"
                            />
                            {errors.password && (
                                <span style={{ color: "red" }}>
                                    {errors.cpassword?.message}
                                </span>
                            )}

                            <div className="form-end">
                                <input
                                    type="submit"
                                    className="button"
                                    value="Register"
                                />
                                <Link to="../login">Déjà un compte ?</Link>
                            </div>
                        </div>
                    </form>
                </section>
            </div>
        </>
    );
}

export default Register;
