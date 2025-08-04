import FactionInfo from "../components/snippets/faction_infos";
import CurrencyInfo from "../components/snippets/currency_info";
import RolesTable from "../components/snippets/roles_table";
import UsersTable from "../components/snippets/userlist";

import "../../assets/css/components/container.css";

export default function FactionDashboard() {
    return (
        <div className="information-container">
            <FactionInfo />
            <CurrencyInfo />
            <UsersTable />
            <RolesTable />
        </div>
    );
}
