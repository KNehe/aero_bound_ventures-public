"use client";

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Toaster } from 'sonner';

export default function Providers({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 60 * 1000,
                        refetchOnWindowFocus: false,
                    },
                },
            }),
    );

    const shouldRenderToaster = pathname !== '/auth/login';

    return (
        <QueryClientProvider client={queryClient}>
            {children}
            {shouldRenderToaster ? <Toaster position="top-right" richColors closeButton /> : null}
        </QueryClientProvider>
    );
}
