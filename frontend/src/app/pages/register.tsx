import { Link } from "react-router-dom";

import { useRegister } from "../components/hooks/auth";

import logo from "../../assets/images/CC_logo.png";

import "../../assets/css/pages/login.css";

function Register() {
    const { form, loading, message, onSubmit } = useRegister();

    const {
        register,
        formState: { errors },
    } = form;

    return (
        <>
            <div className="content">
                <section id="register">
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
                                        <Link to="../login">
                                            Déjà un compte ?
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

export default Register;
