import "../../assets/css/pages/login.css";
import logo from "../../assets/images/CC_logo.png";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import * as Yup from "yup";
import { yupResolver } from "@hookform/resolvers/yup";
import { useAuth } from "../utils/authprovider";
import axios from "axios";

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

    const { setToken } = useAuth() ?? {};

    const onSubmit = handleSubmit(async (data) => {
        try {
            // Replace with your actual API endpoint
            const response = await axios.post(
                "http://127.0.0.1:8000/auth/login",
                data
            );
            if (response.data && response.data.access_token) {
                setToken?.(response.data.access_token); // Save token to context
                console.log("You Are Successfully Logged In");
                // Optionally redirect user here
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
                                <b>Username</b>
                            </label>
                            <input
                                type="username"
                                {...register("username", { required: true })}
                                placeholder="Enter username"
                            />
                            {errors.username && (
                                <span style={{ color: "red" }}>
                                    *Username* is mandatory
                                </span>
                            )}
                            <label>
                                <b>Password</b>
                            </label>
                            <input
                                type="password"
                                {...register("password", { required: true })}
                                placeholder="Enter password"
                            />
                            {errors.password && (
                                <span style={{ color: "red" }}>
                                    *Password* is mandatory
                                </span>
                            )}

                            <div className="form-end">
                                <input
                                    type="submit"
                                    className="button"
                                    value="Log in"
                                />
                                <Link to="../register">
                                    Don't have an account ?
                                </Link>
                            </div>
                        </div>
                    </form>
                </section>
            </div>
        </>
    );
}

export default Login;
