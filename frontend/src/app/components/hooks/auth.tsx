import { useLocation, useNavigate } from "react-router";
import { yupResolver } from "@hookform/resolvers/yup";
import { useForm } from "react-hook-form";
import { useEffect, useState } from "react";

import * as Yup from "yup";
import axios from "axios";

import { useAuth } from "../../utils/authcontext";

import type {
    UserLoginForm,
    UserRegisterData,
    UserRegisterForm,
    AuthLoginHook,
    AuthRegisterHook,
} from "../../types/users";
import type { AuthType } from "../../types/hooks";

const LoginSchema = Yup.object().shape({
    username: Yup.string().required("Username is required"),
    password: Yup.string().required("Password is required"),
});

const RegisterSchema = Yup.object().shape({
    username: Yup.string().required("Username is required"),
    password: Yup.string()
        .required("Password is required")
        .min(4, "Password length should be at least 4 characters")
        .max(40, "Password cannot exceed more than 12 characters"),
    cpassword: Yup.string()
        .required("Confirm Password is required")
        .min(4, "Password length should be at least 4 characters")
        .max(40, "Password cannot exceed more than 12 characters")
        .oneOf([Yup.ref("password")], "Passwords do not match"),
});

function getSafeReturnPath(state: unknown): string {
    if (state && typeof state === "object" && "from" in state) {
        const from = state.from;

        if (from && typeof from === "object" && "pathname" in from) {
            const location = from as {
                pathname?: unknown;
                search?: unknown;
                hash?: unknown;
            };

            if (
                typeof location.pathname === "string" &&
                location.pathname.startsWith("/A.I.D.E")
            ) {
                return `${location.pathname}${typeof location.search === "string" ? location.search : ""}${typeof location.hash === "string" ? location.hash : ""}`;
            }
        }
    }

    return "/A.I.D.E";
}

export function useLogin(): AuthLoginHook {
    const { token, setToken } = useAuth() ?? {};

    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");

    const form = useForm<UserLoginForm>({
        resolver: yupResolver(LoginSchema),
    });

    const onSubmit = form.handleSubmit(async (data: UserLoginForm) => {
        try {
            setLoading(true);
            setMessage("");

            const response = await axios.post<AuthType>("/auth/login", data);

            const accessToken = response.data.access_token;
            setToken?.(accessToken);
            axios.defaults.headers.common["Authorization"] =
                `Bearer ${accessToken}`;

            setMessage("You Are Successfully Logged In");
        } catch (error: unknown) {
            const status = axios.isAxiosError(error)
                ? error.response?.status
                : undefined;
            if (status === 401) {
                setMessage("❌  Mot de passe incorrect");
            } else if (status === 404) {
                setMessage(
                    "❌ Il n'y a pas de compte avec ce nom d'utilisateur",
                );
            } else {
                setMessage(
                    `Login error: ${
                        axios.isAxiosError(error)
                            ? error.message
                            : "Unknown error"
                    }`,
                );
            }
        } finally {
            setLoading(false);
        }
    });

    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        if (!token) return;

        navigate(getSafeReturnPath(location.state), {
            replace: true,
            state: null,
        });
    }, [token, navigate, location.state]);

    return {
        form,
        loading,
        message,
        onSubmit,
    };
}

export function useRegister(): AuthRegisterHook {
    const { token, setToken } = useAuth() ?? {};

    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");

    const form = useForm<UserRegisterForm>({
        resolver: yupResolver(RegisterSchema),
    });

    const onSubmit = form.handleSubmit(async (data: UserRegisterForm) => {
        setLoading(true);
        setMessage("");

        const payload: UserRegisterData = {
            username: data.username,
            password: data.password,
            is_admin: false,
        };

        try {
            const res = await axios.post<AuthType>("/auth/register", payload);

            const accessToken = res.data.access_token;
            setToken?.(accessToken);
            axios.defaults.headers.common["Authorization"] =
                `Bearer ${accessToken}`;

            setMessage("Registration successful!");
        } catch (error: unknown) {
            if (axios.isAxiosError(error) && error.response?.status === 409) {
                setMessage("❌ Un utilisateur possède déjà ce nom");
            } else {
                setMessage(
                    `Registration error: ${
                        axios.isAxiosError(error)
                            ? error.message
                            : "Unknown error"
                    }`,
                );
            }
        } finally {
            setLoading(false);
        }
    });

    const navigate = useNavigate();
    useEffect(() => {
        if (!token) return;

        navigate("/A.I.D.E", { replace: true });
    }, [token, navigate]);

    return {
        form,
        loading,
        message,
        onSubmit,
    };
}
