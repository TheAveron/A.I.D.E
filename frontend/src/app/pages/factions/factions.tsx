import FactionList from "../../components/factions/factionlist";
import PageHeader from "../../components/common/page_header";

function Faction() {
    return (
        <div className="faction-box">
            <PageHeader
                title="Factions"
                description="Les groupes de joueurs du serveur, leurs membres et leurs monnaies. Rejoignez-en une ou fondez la vôtre."
            />
            <FactionList />
        </div>
    );
}

export default Faction;
