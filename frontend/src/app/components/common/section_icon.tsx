import type { ReactNode } from "react";

/** The drawing of each section (24×24, stroked with currentColor). */
const PATHS: Record<string, ReactNode> = {
    economie: (
        <>
            <circle cx="9" cy="9" r="6" />
            <path d="M18.09 10.37A6 6 0 1 1 10.34 18" />
            <path d="M7 6h1v4" />
            <path d="m16.71 13.88.7.71-2.82 2.82" />
        </>
    ),
    reseau: (
        <>
            <rect x="5" y="3" width="14" height="14" rx="3" />
            <path d="M5 11h14M12 3v8" />
            <circle cx="8.5" cy="14" r=".5" />
            <circle cx="15.5" cy="14" r=".5" />
            <path d="m8 21 1.5-4M16 21l-1.5-4" />
        </>
    ),
    ressources: (
        <>
            <path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z" />
            <path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z" />
        </>
    ),
    admin: (
        <>
            <path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5z" />
            <path d="m9 12 2 2 4-4" />
        </>
    ),
};

/** The icon of a section of the site; decorative (hidden from screen readers). */
export default function SectionIcon({
    section,
    className,
}: {
    section: string;
    className?: string;
}) {
    return (
        <svg
            className={className}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
        >
            {PATHS[section]}
        </svg>
    );
}
