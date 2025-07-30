import "../../assets/css/pages/login.css";
import { useForm } from "react-hook-form";
import logo from "../../assets/images/CC_logo.png";
import { Link } from "react-router-dom";
import { yupResolver } from "@hookform/resolvers/yup";
import * as Yup from "yup";
import axios from "axios";
import { useAuth } from "../components/authprovider";

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

    const { setToken } = useAuth() ?? {};

    const onSubmit = handleSubmit(async (data) => {
        try {
            // Replace with your actual API endpoint
            const response = await axios.post(
                "http://localhost:3000/api/auth/register",
                {
                    username: data.username,
                    password: data.password,
                }
            );
            if (response.data && response.data.token) {
                setToken?.(response.data.token);
                console.log("Registration successful!");
                // Optionally redirect user here
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
                                <b>Username</b>
                            </label>
                            <input
                                type="username"
                                {...register("username", { required: true })}
                                placeholder="Enter username"
                            />
                            {errors.username?.message && (
                                <span style={{ color: "red" }}>
                                    *Username* is mandatory,
                                    {errors.username?.message}
                                </span>
                            )}
                            <label>
                                <b>Password</b>
                            </label>
                            <input
                                type="password"
                                {...register("password")}
                                placeholder="Enter password"
                            />
                            {errors.password && (
                                <span style={{ color: "red" }}>
                                    {errors.password?.message}
                                </span>
                            )}
                            <label>
                                <b>Password confirmation</b>
                            </label>
                            <input
                                type="password"
                                {...register("cpassword")}
                                placeholder="Enter password"
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
                                    Already have an account ?
                                </Link>
                            </div>
                        </div>
                    </form>
                </section>
            </div>
        </>
    );
}

export default Register;
