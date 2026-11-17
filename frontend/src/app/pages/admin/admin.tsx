import { useState } from "react";
import { Link } from "react-router";

import { useMe } from "../../hooks/users/me";
import AdminAudit from "../../components/admin/admin_audit";
import AdminCurrencies from "../../components/admin/admin_currencies";
import AdminFactions from "../../components/admin/admin_factions";
import AdminOffers from "../../components/admin/admin_offers";
import AdminTransactions from "../../components/admin/admin_transactions";
import AdminUsers from "../../components/admin/admin_users";

type Tab =
    | "users"
    | "factions"
    | "offers"
    | "transactions"
    | "currencies"
    | "trains"
    | "audit";

/** The administration panel; the tabs shown depend on the server-wide roles. */
export default function AdminPage() {
    const { user, loading, error } = useMe();
    const [requested, setTab] = useState<Tab | null>(null);

    if (error) return <p role="alert">{error}</p>;
    if (loading || !user) return <p>Chargement...</p>;

    const isAdmin = user.global_roles?.includes("admin") ?? false;
    const isTrainAdmin = user.global_roles?.includes("train_admin") ?? false;

    if (!isAdmin && !isTrainAdmin) {
        return (
            <div className="information-container">
                <div className="snippet-container">
                    <h2>Administration</h2>
                    <p>Cette page est réservée à l&apos;équipe du serveur.</p>
                </div>
            </div>
        );
    }

    const tabs: [Tab, string][] = [
        ...(isAdmin
            ? ([
                  ["users", "Comptes"],
                  ["factions", "Factions"],
                  ["offers", "Offres"],
                  ["transactions", "Transactions"],
                  ["currencies", "Monnaies"],
              ] as [Tab, string][])
            : []),
        ["trains", "Trains, lignes et gares"],
        ["audit", "Journal"],
    ];
    const tab = tabs.some(([value]) => value === requested)
        ? requested
        : tabs[0][0];

    return (
        <div className="information-container">
            <div className="snippet-container">
                <h2>Administration</h2>
                <div className="toolbar" role="tablist">
                    {tabs.map(([value, label]) => (
                        <button
                            key={value}
                            type="button"
                            role="tab"
                            aria-selected={tab === value}
                            className="button"
                            disabled={tab === value}
                            onClick={() => setTab(value)}
                        >
                            {label}
                        </button>
                    ))}
                </div>
            </div>

            {tab === "users" && isAdmin && <AdminUsers />}
            {tab === "factions" && isAdmin && <AdminFactions />}
            {tab === "offers" && isAdmin && <AdminOffers />}
            {tab === "transactions" && isAdmin && <AdminTransactions />}
            {tab === "currencies" && isAdmin && <AdminCurrencies />}
            {tab === "trains" && (
                <div className="snippet-container">
                    <h2>Trains, lignes et gares</h2>
                    <p>
                        {isTrainAdmin
                            ? "En tant qu'admin trains, vous pouvez modifier ou retirer tous les trains, lignes et gares depuis leurs pages. Ces actions sont inscrites au journal."
                            : "Seul un admin trains peut modifier les trains, lignes et gares des autres. Donnez ce rôle depuis l'onglet Comptes."}
                    </p>
                    <div className="toolbar">
                        <Link className="button" to="/trains">
                            Trains
                        </Link>
                        <Link className="button" to="/lines">
                            Lignes
                        </Link>
                        <Link className="button" to="/stations">
                            Gares
                        </Link>
                    </div>
                </div>
            )}
            {tab === "audit" && <AdminAudit />}
        </div>
    );
}
