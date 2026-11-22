import FactionInfo from "../../components/factions/faction_infos";
import CurrencyInfo from "../../components/currencies/currency_info";
import RolesTable from "../../components/factions/roles_table";
import UsersTable from "../../components/users/userlist";

import TransactionsTable from "../../components/transactions/transaction_table";
import { useParams } from "react-router";
import { useMe } from "../../hooks/users/me";
import { useRole } from "../../hooks/factions/role";
import HistoryTable from "../../components/transactions/history_table";
import OfferList from "../../components/offers/offerslist";
import { useRoles } from "../../hooks/factions/factionroles";
import FactionDocuments from "../../components/factions/faction_documents";
import JoinRequestsPanel from "../../components/factions/join_requests_panel";

export default function FactionDashboard() {
    const { factionid } = useParams();

    const { user } = useMe();
    const { role } = useRole(user?.role_id ?? null);
    const { roles } = useRoles(factionid ?? null);

    const active = role?.view_transactions ?? false;
    // Same rule as the API (crud/offer_history): view_transactions in this faction
    const canSeeHistory =
        !!factionid &&
        !!role?.view_transactions &&
        role.faction_id === Number(factionid) &&
        user?.faction_id === Number(factionid);
    const canHandleRequests =
        !!factionid &&
        !!role?.handle_members &&
        role.faction_id === Number(factionid);

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
            {canHandleRequests && <JoinRequestsPanel factionId={factionid} />}
            {factionid && <FactionDocuments factionId={factionid} />}
            <OfferList
                factionId={factionid}
                offersPerPage={7}
                canCreate={user?.faction_id === Number(factionid)}
            />
            {role?.view_transactions ? (
                <TransactionsTable factionId={factionid} />
            ) : (
                <></>
            )}
            {canSeeHistory && (
                <HistoryTable factionId={factionid} HistoriesPerPage={7} />
            )}
        </div>
    );
}
