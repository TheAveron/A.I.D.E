import { useRef, type KeyboardEvent, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router";

import { useMe } from "../../hooks/users/me";
import { useAdminOverview } from "../../hooks/admin/admin";
import AdminAudit from "../../components/admin/admin_audit";
import AdminCurrencies from "../../components/admin/admin_currencies";
import AdminFactions from "../../components/admin/admin_factions";
import AdminOffers from "../../components/admin/admin_offers";
import AdminTransactions from "../../components/admin/admin_transactions";
import AdminUsers from "../../components/admin/admin_users";
import PageHeader from "../../components/common/page_header";

type Tab =
    | "apercu"
    | "comptes"
    | "factions"
    | "offres"
    | "transactions"
    | "monnaies"
    | "trains"
    | "journal";

const ROLE_LABELS: Record<string, string> = {
    admin: "Admin",
    train_admin: "Admin trains",
    money_admin: "Admin monnaies",
};

const ADMIN_SECTION = { id: "admin", label: "Administration" };

/** The administration panel; the tabs shown depend on the server-wide roles. */
export default function AdminPage() {
    const { user, loading, error } = useMe();
    const [params, setParams] = useSearchParams();
    const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

    if (error) return <p role="alert">{error}</p>;
    if (loading || !user) return <p>Chargement...</p>;

    const roles = user.global_roles ?? [];
    const isAdmin = roles.includes("admin");
    const isTrainAdmin = roles.includes("train_admin");
    const isMoneyAdmin = roles.includes("money_admin");

    if (!isAdmin && !isTrainAdmin && !isMoneyAdmin) {
        return (
            <div className="information-container">
                <PageHeader
                    section={ADMIN_SECTION}
                    title="Accès réservé"
                    description="Cette page est réservée à l'équipe du serveur."
                />
            </div>
        );
    }

    const tabs: [Tab, string][] = [
        ["apercu", "Aperçu"],
        ...(isAdmin
            ? ([
                  ["comptes", "Comptes"],
                  ["factions", "Factions"],
                  ["offres", "Offres"],
                  ["transactions", "Transactions"],
              ] as [Tab, string][])
            : []),
        ...(isAdmin || isMoneyAdmin
            ? ([["monnaies", "Monnaies"]] as [Tab, string][])
            : []),
        ...(isAdmin || isTrainAdmin
            ? ([["trains", "Réseau ferré"]] as [Tab, string][])
            : []),
        ["journal", "Journal"],
    ];
    const requested = params.get("onglet");
    const tab: Tab = tabs.some(([value]) => value === requested)
        ? (requested as Tab)
        : "apercu";

    // The tab lives in the address: a reload or a shared link keeps it
    const select = (value: Tab, focus = false) => {
        const next = new URLSearchParams(params);
        if (value === "apercu") next.delete("onglet");
        else next.set("onglet", value);
        setParams(next, { replace: true });
        if (focus) tabRefs.current[value]?.focus();
    };

    // Arrows, Home and End move between tabs (the ARIA tabs pattern)
    const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
        const index = tabs.findIndex(([value]) => value === tab);
        const moves: Record<string, number> = {
            ArrowRight: index + 1,
            ArrowLeft: index - 1,
            Home: 0,
            End: tabs.length - 1,
        };
        if (!(event.key in moves)) return;
        event.preventDefault();
        const target = (moves[event.key] + tabs.length) % tabs.length;
        select(tabs[target][0], true);
    };

    return (
        <div className="information-container admin-page">
            <PageHeader
                section={ADMIN_SECTION}
                title="Panneau d'administration"
                description={
                    <>
                        Connecté en tant que{" "}
                        {roles.map((r) => ROLE_LABELS[r] ?? r).join(", ")}.
                        Les actions sur ce qui appartient à d&apos;autres
                        joueurs sont inscrites au journal.
                    </>
                }
            />

            <div
                className="admin-tabs"
                role="tablist"
                aria-label="Sections de l'administration"
                onKeyDown={onKeyDown}
            >
                {tabs.map(([value, label]) => (
                    <button
                        key={value}
                        ref={(el) => {
                            tabRefs.current[value] = el;
                        }}
                        id={`admin-tab-${value}`}
                        type="button"
                        role="tab"
                        aria-selected={tab === value}
                        aria-controls="admin-panel"
                        tabIndex={tab === value ? 0 : -1}
                        onClick={() => select(value)}
                    >
                        {label}
                    </button>
                ))}
            </div>

            <div
                id="admin-panel"
                className="admin-panel"
                role="tabpanel"
                aria-labelledby={`admin-tab-${tab}`}
            >
                {tab === "apercu" && (
                    <AdminOverview
                        isAdmin={isAdmin}
                        canTrains={isAdmin || isTrainAdmin}
                        onOpen={select}
                    />
                )}
                {tab === "comptes" && isAdmin && <AdminUsers />}
                {tab === "factions" && isAdmin && <AdminFactions />}
                {tab === "offres" && isAdmin && <AdminOffers />}
                {tab === "transactions" && isAdmin && <AdminTransactions />}
                {tab === "monnaies" && (isAdmin || isMoneyAdmin) && (
                    <AdminCurrencies />
                )}
                {tab === "trains" && <AdminTrains isTrainAdmin={isTrainAdmin} />}
                {tab === "journal" && <AdminAudit />}
            </div>
        </div>
    );
}

/** The first tab: the size of things, and what is waiting for the staff. */
function AdminOverview({
    isAdmin,
    canTrains,
    onOpen,
}: {
    isAdmin: boolean;
    canTrains: boolean;
    onOpen: (tab: Tab) => void;
}) {
    const { overview, loading, error } = useAdminOverview();

    if (error) return <p role="alert">{error}</p>;
    if (loading || !overview) return <p>Chargement...</p>;

    const tiles: { label: string; value: number; hint?: ReactNode }[] = [
        { label: "Comptes", value: overview.users, hint: `dont ${overview.staff} dans l'équipe` },
        { label: "Factions approuvées", value: overview.factions },
        { label: "Offres ouvertes", value: overview.offers_open },
        { label: "Schematics", value: overview.schematics },
        { label: "Actions au journal", value: overview.audit_last_week, hint: "ces 7 derniers jours" },
    ];

    return (
        <div className="admin-overview">
            {isAdmin && overview.factions_pending > 0 ? (
                <div className="admin-todo" role="status">
                    <p>
                        <strong>
                            {overview.factions_pending} faction
                            {overview.factions_pending > 1 ? "s attendent" : " attend"}{" "}
                            votre approbation.
                        </strong>{" "}
                        Tant qu&apos;elle n&apos;est pas approuvée, une faction
                        n&apos;apparaît pas dans la liste publique.
                    </p>
                    <button
                        type="button"
                        className="button"
                        onClick={() => onOpen("factions")}
                    >
                        Voir les factions en attente
                    </button>
                </div>
            ) : (
                <p className="admin-all-clear">✓ Rien n&apos;attend votre intervention.</p>
            )}

            <dl className="admin-tiles">
                {tiles.map((t) => (
                    <div key={t.label}>
                        <dt>{t.label}</dt>
                        <dd>{t.value.toLocaleString()}</dd>
                        {t.hint && <dd className="admin-tile-hint">{t.hint}</dd>}
                    </div>
                ))}
            </dl>

            <div className="admin-shortcuts">
                <h2>Raccourcis</h2>
                <ul>
                    {isAdmin && (
                        <li>
                            <button type="button" className="link-button" onClick={() => onOpen("comptes")}>
                                Gérer les comptes et les rôles
                            </button>
                        </li>
                    )}
                    {canTrains && (
                        <li>
                            <Link to="/lines">Lignes, gares et trains</Link>
                        </li>
                    )}
                    <li>
                        <Link to="/schematiques">Galerie de schematics</Link>{" "}
                        <span className="admin-note">
                            (un admin peut supprimer un schematic depuis sa page)
                        </span>
                    </li>
                    <li>
                        <button type="button" className="link-button" onClick={() => onOpen("journal")}>
                            Consulter le journal
                        </button>
                    </li>
                </ul>
            </div>
        </div>
    );
}

function AdminTrains({ isTrainAdmin }: { isTrainAdmin: boolean }) {
    return (
        <div className="snippet-container">
            <h2>Réseau ferré</h2>
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
    );
}
