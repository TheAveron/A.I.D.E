import { useMemo, useState } from "react";

/** Client-side paging of `items`; the page never goes past the last one. */
export function usePagination<T>(items: T[], perPage: number) {
    const [requestedPage, setPage] = useState(1);

    const totalPages = Math.max(Math.ceil(items.length / perPage), 1);
    const page = Math.min(Math.max(requestedPage, 1), totalPages);

    const pageItems = useMemo(
        () => items.slice((page - 1) * perPage, page * perPage),
        [items, page, perPage],
    );

    return { pageItems, page, totalPages, setPage };
}
