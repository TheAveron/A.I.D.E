import type { ComponentProps } from "react";

/**
 * A markdown table: the wrapper scrolls on a narrow screen, so the table
 * itself can fill the reading column.
 */
export default function MarkdownTable({ children }: ComponentProps<"table">) {
    return (
        <div className="markdown-table">
            <table>{children}</table>
        </div>
    );
}
