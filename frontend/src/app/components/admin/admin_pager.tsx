import { ADMIN_PAGE } from "../../hooks/admin/admin";

/** Previous / next for the admin lists (a full page means there may be more). */
export default function AdminPager({
    page,
    count,
    setPage,
}: {
    page: number;
    count: number;
    setPage: (page: number) => void;
}) {
    return (
        <div className="pagination-controls">
            <button
                type="button"
                className="button"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
            >
                Précédent
            </button>
            <span>Page {page}</span>
            <button
                type="button"
                className="button"
                disabled={count < ADMIN_PAGE}
                onClick={() => setPage(page + 1)}
            >
                Suivant
            </button>
        </div>
    );
}
