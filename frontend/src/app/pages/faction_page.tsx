import FactionInfo from "../components/snippets/faction_infos";
import CurrencyInfo from "../components/snippets/currency_info";
import RolesTable from "../components/snippets/roles_table";
import UsersTable from "../components/snippets/userlist";

import TransactionsTable from "../components/snippets/transaction_table";
import { useParams } from "react-router-dom";
import { useMe } from "../components/hooks/me";
import { useRole } from "../components/hooks/role";
import HistoryTable from "../components/snippets/history_table";
import OfferList from "../components/offerslist";
import { useEffect, useState } from "react";
import { useRoles } from "../components/hooks/factionroles";

export default function FactionDashboard() {
    const { factionid } = useParams();

    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);
    const { roles } = useRoles(factionid ?? null);

    const [active, setActive] = useState(false);

    useEffect(() => setActive(role?.view_transactions ?? false));

    return (
        <div className="information-container">
            <FactionInfo factionId={factionid ?? null} />
            <CurrencyInfo />
            <UsersTable state={active} />
            {role &&
            roles?.map((r) => r.role_id).includes(role.role_id) &&
            role?.manage_roles ? (
                <RolesTable />
            ) : (
                <></>
            )}
            <OfferList factionId={factionid} offersPerPage={7} />
            {role?.view_transactions ? <TransactionsTable /> : <></>}
            {role &&
            roles?.map((r) => r.role_id).includes(role.role_id) &&
            ["Chef", "Chef Adjoint"].includes(role?.name ?? "") ? (
                <HistoryTable factionId={factionid} HistoriesPerPage={7} />
            ) : (
                <></>
            )}
        </div>
    );
}
