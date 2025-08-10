import { useNavigate } from "react-router-dom";
import { yupResolver } from "@hookform/resolvers/yup";
import { useForm } from "react-hook-form";
import { useState } from "react";

import * as Yup from "yup";
import axios from "axios";

import { useAuth } from "../../utils/authprovider";

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

            setToken?.(response.data.access_token);
            axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;

            setMessage("You Are Successfully Logged In");
        } catch (error: any) {
            if (error.response?.status === 401) {
                setMessage("❌  Mot de passe incorrect");
            } else if (error.response?.status === 404) {
                setMessage(
                    "❌ Il n'y a pas de compte avec ce nom d'utilisateur"
                );
            } else {
                setMessage(`Login error: ${error.message}`);
            }
        } finally {
            setLoading(false);
        }
    });

    const navigate = useNavigate();
    if (token) {
        navigate("/A.I.D.E");
    }

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

            setToken?.(res.data.access_token);
            axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;

            setMessage("Registration successful!");
        } catch (error: any) {
            if (error.response?.status === 409) {
                setMessage("❌ Un utilisateur possède déjà ce nom");
            } else {
                setMessage(`Registration error: ${error.message}`);
            }
        } finally {
            setLoading(false);
        }
    });

    const navigate = useNavigate();
    if (token) {
        navigate("/A.I.D.E");
    }

    return {
        form,
        loading,
        message,
        onSubmit,
    };
}
