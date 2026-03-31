"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import useAuth from "@/store/auth";
import { ADMIN_GROUP_NAME, MIN_PASSWORD_LENGTH } from "@/constants/auth";
import { LoginResponse } from "@/types/auth";
import { ApiClientError, apiClient, getApiBaseUrl } from "@/lib/api";

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
    mutationFn: async () => {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      return apiClient.postForm<LoginResponse>("/token", formData);
    },
    onSuccess: (data) => {
      setUser(data.user);
      toast.success("Signed in successfully");
      router.push(getRedirectTarget(redirectTo, data.user.groups));
    },
    onError: (err: unknown) => {
      const message =
        err instanceof ApiClientError
          ? err.detail || "Invalid email or password"
          : err instanceof Error
            ? err.message
            : "Login failed. Please try again.";

      setError(message);
      toast.error("Unable to sign in", { description: message });
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
      toast.success("Account created", {
        description: "Signing you in now.",
      });
      loginMutation.mutate();
    },
    onError: (err: unknown) => {
      const message =
        err instanceof ApiClientError
          ? err.detail || "Registration failed"
          : err instanceof Error
            ? err.message
            : "Signup failed. Please try again.";

      setError(message);
      toast.error("Unable to create account", { description: message });
    },
    onMutate: () => {
      setError("");
    },
  });

  const handleLogin = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    loginMutation.mutate();
  };

  const handleSignup = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      const message = "Passwords do not match";
      setError(message);
      toast.error(message);
      return;
    }

    if (password.length < MIN_PASSWORD_LENGTH) {
      const message = `Password must be at least ${MIN_PASSWORD_LENGTH} characters long`;
      setError(message);
      toast.error("Password is too short", { description: message });
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
