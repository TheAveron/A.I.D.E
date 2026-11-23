import OfferList from "../../components/offers/offerslist";
import PageHeader from "../../components/common/page_header";

function Offers() {
    return (
        <div className="offer-box">
            <PageHeader
                title="Marché"
                description="Les offres d'achat et de vente des joueurs et des factions. Acceptez-en une ou publiez la vôtre."
            />
            <OfferList offersPerPage={20} />
        </div>
    );
}

export default Offers;
