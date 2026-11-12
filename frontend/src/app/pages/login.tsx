import { Link } from "react-router";

import { useLogin } from "../components/hooks/auth";

import logo from "../../assets/images/CC_logo.png";

import "../../assets/css/pages/login.css";

function Login() {
    const { form, loading, message, onSubmit } = useLogin();

    const {
        register,
        formState: { errors },
    } = form;

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
                            {message && (
                                <p role="alert" style={{ color: "red" }}>
                                    {message}
                                </p>
                            )}
                            <label htmlFor="login-username">
                                <b>Nom d'utilisateur</b>
                            </label>
                            <input
                                id="login-username"
                                type="text"
                                autoComplete="username"
                                {...register("username", {
                                    required: true,
                                })}
                                placeholder="Entrer votre nom"
                            />
                            {errors.username && (
                                <span style={{ color: "red" }}>
                                    *Nom* obligatoire
                                </span>
                            )}
                            <label htmlFor="login-password">
                                <b>Mot de passe</b>
                            </label>
                            <input
                                id="login-password"
                                type="password"
                                autoComplete="current-password"
                                {...register("password", {
                                    required: true,
                                })}
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
                                    value={
                                        loading ? "Chargement ..." : "Log in"
                                    }
                                    disabled={loading}
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
