"use client";
import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import NProgress from "nprogress";

NProgress.configure({ showSpinner: false, speed: 400, minimum: 0.2 });

export default function NavigationProgress() {
    const pathname = usePathname();
    const searchParams = useSearchParams();

    useEffect(() => {
        NProgress.done();
    }, [pathname, searchParams]);

    useEffect(() => {
        const handleClick = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            const anchor = target.closest("a");
            if (
                anchor &&
                anchor.href &&
                anchor.target !== "_blank" &&
                !anchor.href.startsWith("#") &&
                !anchor.href.startsWith("mailto:") &&
                !anchor.href.startsWith("tel:") &&
                !anchor.href.startsWith("https://wa.me") &&
                new URL(anchor.href).origin === window.location.origin
            ) {
                NProgress.start();
            }
        };

        document.addEventListener("click", handleClick);
        return () => document.removeEventListener("click", handleClick);
    }, []);

    return null;
}
