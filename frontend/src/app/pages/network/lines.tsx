import { Link } from "react-router";

import { useLines } from "../../hooks/network/trains";
import { useTrainRights } from "../../hooks/network/trainrights";
import LineSwatch from "../../components/network/line_swatch";
import NewLine from "../../components/network/new_line";
import PageHeader from "../../components/common/page_header";

/** All the lines, with their two ends. */
export default function LinesPage() {
    const { lines, loading, error } = useLines();
    const rights = useTrainRights();
    const canCreate = rights.isTrainAdmin || rights.factionId !== null;

    return (
        <div className="information-container">
            <PageHeader
                title="Lignes"
                description="Les lignes du réseau, de terminus à terminus, avec le nombre de gares desservies."
                actions={canCreate && <NewLine />}
            />
            <div className="snippet-container">
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Ligne</th>
                                <th>Nom</th>
                                <th>De</th>
                                <th>À</th>
                                <th>Gares</th>
                            </tr>
                        </thead>
                        <tbody>
                            {error ? (
                                <tr>
                                    <td colSpan={5}>{error}</td>
                                </tr>
                            ) : loading ? (
                                <tr>
                                    <td colSpan={5}>Chargement...</td>
                                </tr>
                            ) : lines.length === 0 ? (
                                <tr className="empty-state">
                                    <td colSpan={5}>
                                        Aucune ligne pour l&apos;instant.
                                    </td>
                                </tr>
                            ) : (
                                lines.map((line) => {
                                    const first = line.stops[0]?.station;
                                    const last =
                                        line.stops[line.stops.length - 1]
                                            ?.station;
                                    return (
                                        <tr key={line.code}>
                                            <td>
                                                <Link to={`/line/${line.code}`}>
                                                    <LineSwatch
                                                        code={line.code}
                                                        color={line.color}
                                                    />
                                                </Link>
                                            </td>
                                            <td>{line.name ?? "-"}</td>
                                            <td>{first?.name ?? "-"}</td>
                                            <td>
                                                {line.stops.length > 1
                                                    ? last?.name
                                                    : "-"}
                                            </td>
                                            <td>{line.stops.length}</td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
