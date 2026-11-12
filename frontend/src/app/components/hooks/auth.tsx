import { useLocation, useNavigate } from "react-router";
import { yupResolver } from "@hookform/resolvers/yup";
import { useForm } from "react-hook-form";
import { useEffect, useState } from "react";

import * as Yup from "yup";
import axios from "axios";

import { useAuth } from "../../utils/authcontext";
import { applyAuthHeader } from "../../utils/authheader";
import { getErrorMessage } from "../../utils/apierror";
import { getSafeReturnPath } from "../../utils/returnpath";

import type {
    UserLoginForm,
    UserRegisterData,
    UserRegisterForm,
    AuthLoginHook,
    AuthRegisterHook,
} from "../../types/users";
import type { AuthType } from "../../types/hooks";

// The server's limits: 50 characters for a name, 72 bytes for a password.
const USERNAME_MAX = 50;
const PASSWORD_MIN = 4;
const PASSWORD_MAX = 40;

const LoginSchema = Yup.object().shape({
    username: Yup.string().required("Username is required"),
    password: Yup.string().required("Password is required"),
});

const RegisterSchema = Yup.object().shape({
    username: Yup.string()
        .required("Username is required")
        .max(
            USERNAME_MAX,
            `Username cannot exceed more than ${USERNAME_MAX} characters`,
        ),
    password: Yup.string()
        .required("Password is required")
        .min(
            PASSWORD_MIN,
            `Password length should be at least ${PASSWORD_MIN} characters`,
        )
        .max(
            PASSWORD_MAX,
            `Password cannot exceed more than ${PASSWORD_MAX} characters`,
        ),
    cpassword: Yup.string()
        .required("Confirm Password is required")
        .min(
            PASSWORD_MIN,
            `Password length should be at least ${PASSWORD_MIN} characters`,
        )
        .max(
            PASSWORD_MAX,
            `Password cannot exceed more than ${PASSWORD_MAX} characters`,
        )
        .oneOf([Yup.ref("password")], "Passwords do not match"),
});

/** The notice RequireAuth/AuthProvider attach to the navigation to /login. */
function getNotice(state: unknown): string {
    if (state && typeof state === "object" && "message" in state) {
        const { message } = state;
        if (typeof message === "string") return message;
    }

    return "";
}

export function useLogin(): AuthLoginHook {
    const { token, setToken } = useAuth() ?? {};
    const navigate = useNavigate();
    const location = useLocation();

    const [loading, setLoading] = useState(false);
    // Starts with the reason the user was sent here (e.g. session expired).
    const [message, setMessage] = useState(() => getNotice(location.state));

    const form = useForm<UserLoginForm>({
        resolver: yupResolver(LoginSchema),
    });

    const onSubmit = form.handleSubmit(async (data: UserLoginForm) => {
        try {
            setLoading(true);
            setMessage("");

            const response = await axios.post<AuthType>("/auth/login", data);

            const accessToken = response.data.access_token;
            applyAuthHeader(accessToken);
            setToken?.(accessToken);
            // The effect below takes the user away from this page.
        } catch (error: unknown) {
            const status = axios.isAxiosError(error)
                ? error.response?.status
                : undefined;

            if (status === 401) {
                // The server doesn't say which of the two was wrong.
                setMessage("❌ Nom d'utilisateur ou mot de passe incorrect");
            } else if (status === 429) {
                setMessage(
                    "❌ Trop de tentatives échouées, réessayez dans quelques minutes",
                );
            } else {
                setMessage(`❌ ${getErrorMessage(error)}`);
            }
        } finally {
            setLoading(false);
        }
    });

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
    const navigate = useNavigate();

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
        };

        try {
            const res = await axios.post<AuthType>("/auth/register", payload);

            const accessToken = res.data.access_token;
            applyAuthHeader(accessToken);
            setToken?.(accessToken);
            // The effect below takes the user away from this page.
        } catch (error: unknown) {
            if (axios.isAxiosError(error) && error.response?.status === 409) {
                setMessage("❌ Un utilisateur possède déjà ce nom");
            } else {
                setMessage(`❌ ${getErrorMessage(error)}`);
            }
        } finally {
            setLoading(false);
        }
    });

    useEffect(() => {
        if (!token) return;

        navigate("/", { replace: true });
    }, [token, navigate]);

    return {
        form,
        loading,
        message,
        onSubmit,
    };
}
