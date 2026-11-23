import { useState } from "react";
import { Link } from "react-router";

import { usePublicLines } from "../../hooks/network/map";
import LineDiagram from "../../components/network/line_diagram";
import PageHeader from "../../components/common/page_header";

/** The train network as linear metro strips, one per line. Public. */
export default function NetworkPage() {
    const { lines, loading, error } = usePublicLines();
    const [selected, setSelected] = useState("");

    const shown = selected ? lines.filter((l) => l.code === selected) : lines;

    return (
        <div className="information-container">
            <PageHeader
                title="Plan du réseau"
                description="Chaque ligne et ses gares, dans l'ordre, comme sur un plan de métro."
                actions={
                    <Link className="button" to="/actual">
                        Voir sur la carte
                    </Link>
                }
            />
            <div className="snippet-container network-header">
                <label>
                    Ligne{" "}
                    <select
                        value={selected}
                        onChange={(e) => setSelected(e.target.value)}
                    >
                        <option value="">Toutes les lignes</option>
                        {lines.map((l) => (
                            <option key={l.line_id} value={l.code}>
                                {l.name ? `${l.code} - ${l.name}` : l.code}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            {error ? (
                <p role="alert">{error}</p>
            ) : loading ? (
                <p>Chargement...</p>
            ) : shown.length === 0 ? (
                <p className="empty-state">Aucune ligne pour l&apos;instant.</p>
            ) : (
                shown.map((line) => (
                    <div
                        className="snippet-container network-line"
                        key={line.line_id}
                    >
                        <LineDiagram line={line} allLines={lines} />
                    </div>
                ))
            )}
        </div>
    );
}
