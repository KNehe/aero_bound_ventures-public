"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import useAuth from "@/store/auth";
import { ADMIN_GROUP_NAME } from "@/constants/auth";

interface User {
    id: string;
    email: string;
    is_active: boolean;
    is_superuser: boolean;
    auth_provider: string;
    groups: { id: string; name: string }[];
}

export default function GoogleCallbackPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const setUser = useAuth((state) => state.setUser);
    const [error, setError] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(true);

    useEffect(() => {
        const processCallback = async () => {
            // Note: Token is now set as HTTP-only cookie by the backend redirect
            // We only receive user data in the URL params
            const userParam = searchParams.get("user");
            const errorParam = searchParams.get("error");

            if (errorParam) {
                setError(`OAuth error: ${errorParam}`);
                setIsProcessing(false);
                return;
            }

            if (!userParam) {
                setError("Missing authentication data");
                setIsProcessing(false);
                return;
            }

            try {
                const user: User = JSON.parse(userParam);

                const authUser = {
                    id: user.id,
                    email: user.email,
                    groups: user.groups.map((g) => ({
                        name: g.name,
                        permissions: [],
                    })),
                };

                setUser(authUser);

                const redirectTo = searchParams.get("redirect");

                if (redirectTo && redirectTo !== "/") {
                    router.push(redirectTo);
                } else {
                    const isAdmin = user.groups.some((g) => g.name === ADMIN_GROUP_NAME);
                    if (isAdmin) {
                        router.push("/admin");
                    } else {
                        router.push("/");
                    }
                }
            } catch (err) {
                console.error("Error processing OAuth callback:", err);
                setError("Failed to process authentication");
                setIsProcessing(false);
            }
        };

        processCallback();
    }, [searchParams, setUser, router]);

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
                    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </div>
                    <h1 className="text-xl font-semibold text-gray-900 mb-2">Authentication Failed</h1>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <button
                        onClick={() => router.push("/auth")}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    if (isProcessing) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Completing sign in...</p>
                </div>
            </div>
        );
    }

    return null;
}
