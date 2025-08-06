import { Link } from "react-router-dom";

import logo from "../../assets/images/CC_logo.png";

import "../../assets/css/pages/login.css";
import { useLogin } from "../components/hooks/auth";

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
                    {!message ? (
                        !loading ? (
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
                                    <label>
                                        <b>Mot de passe</b>
                                    </label>
                                    <input
                                        type="password"
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
                                            value="Log in"
                                        />
                                        <Link to="../register">
                                            Pas de compte ?
                                        </Link>
                                    </div>
                                </div>
                            </form>
                        ) : (
                            <p>Chargement ...</p>
                        )
                    ) : (
                        message
                    )}
                </section>
            </div>
        </>
    );
}

export default Login;
