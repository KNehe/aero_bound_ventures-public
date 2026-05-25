"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import useAuth from "@/store/auth";
import { ADMIN_GROUP_NAME, MIN_PASSWORD_LENGTH } from "@/constants/auth";
import { LoginResponse } from "@/types/auth";
import {
  getApiErrorMessage,
  apiClient,
  getApiBaseUrl,
} from "@/lib/api";

type AuthMode = "login" | "signup";

function getRedirectTarget(
  redirectTo: string,
  groups: Array<{ name: string }>
): string {
  if (redirectTo && redirectTo !== "/") {
    return redirectTo;
  }

  const isAdmin = groups.some((group) => group.name === ADMIN_GROUP_NAME);
  return isAdmin ? "/admin" : "/";
}

export function useLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/";

  const { setUser, isAuthenticated, isHydrated } = useAuth();

  const [mode, setMode] = useState<AuthMode>("login");
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleAuthenticatedRedirect = (groups: Array<{ name: string }>) => {
    router.push(getRedirectTarget(redirectTo, groups));
  };

  useEffect(() => {
    if (!isHydrated || !isAuthenticated) {
      return;
    }

    const userInfo = useAuth.getState().userInfo;
    if (!userInfo) {
      return;
    }

    router.push(getRedirectTarget(redirectTo, userInfo.groups));
  }, [isAuthenticated, isHydrated, redirectTo, router]);

  const loginMutation = useMutation({
    mutationFn: async ({
      loginEmail,
      loginPassword,
    }: {
      loginEmail: string;
      loginPassword: string;
    }) => {
      const formData = new URLSearchParams();
      formData.append("username", loginEmail);
      formData.append("password", loginPassword);

      return apiClient.postForm<LoginResponse>("/token", formData);
    },
    onSuccess: (data) => {
      setUser(data.user);
      handleAuthenticatedRedirect(data.user.groups);
    },
    onError: (err: unknown) => {
      setError(
        getApiErrorMessage(err, {
          unauthorizedMessage: "Incorrect email or password.",
        })
      );
    },
    onMutate: () => {
      setError("");
    },
  });

  const signupMutation = useMutation({
    mutationFn: () =>
      apiClient.post("/register/", {
        email,
        password,
      }),
    onSuccess: () => {
      loginMutation.mutate({ loginEmail: email, loginPassword: password });
    },
    onError: (err: unknown) => {
      setError(getApiErrorMessage(err));
    },
    onMutate: () => {
      setError("");
    },
  });

  const handleLogin = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (loginMutation.isPending) {
      return;
    }

    const formData = new FormData(event.currentTarget);
    const loginEmail = String(formData.get("email") || "").trim();
    const loginPassword = String(formData.get("password") || "");

    loginMutation.mutate({ loginEmail, loginPassword });
  };

  const handleSignup = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      const message = "Passwords do not match";
      setError(message);
      return;
    }

    if (password.length < MIN_PASSWORD_LENGTH) {
      const message = `Password must be at least ${MIN_PASSWORD_LENGTH} characters long`;
      setError(message);
      return;
    }

    signupMutation.mutate();
  };

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setError("");
  };

  const startGoogleAuth = () => {
    const redirect =
      redirectTo !== "/" ? `?redirect=${encodeURIComponent(redirectTo)}` : "";
    window.location.href = `${getApiBaseUrl()}/auth/google${redirect}`;
  };

  return {
    mode,
    error,
    email,
    password,
    confirmPassword,
    showPassword,
    showConfirmPassword,
    isHydrated,
    isPending: loginMutation.isPending || signupMutation.isPending,
    switchMode,
    setEmail,
    setPassword,
    setConfirmPassword,
    setShowPassword,
    setShowConfirmPassword,
    handleLogin,
    handleSignup,
    startGoogleAuth,
  };
}
