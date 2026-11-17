export function Pagination({
    page,
    totalPages,
    setPage,
}: {
    page: number;
    totalPages: number;
    setPage: (page: number) => void;
}) {
    if (totalPages <= 1) return null;

    return (
        <div className="pagination-controls">
            <button
                type="button"
                className="button"
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
            >
                Précédent
            </button>
            <span>
                Page {page} / {totalPages}
            </span>
            <button
                type="button"
                className="button"
                onClick={() => setPage(page + 1)}
                disabled={page >= totalPages}
            >
                Suivant
            </button>
        </div>
    );
}
