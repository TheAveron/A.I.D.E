import type { TrainService } from "../../types/trains";
import { SERVICE_NAMES, MAINTENANCE_LINE } from "../../utils/trains";

/** The name as a station board shows it, with its parts. */
export default function TrainBoard({
    name,
    line,
    service,
    number,
    numberNote,
}: {
    name: string;
    line: string;
    service: TrainService | "" | null;
    number: number | null;
    numberNote?: string;
}) {
    const isMaintenance = line === MAINTENANCE_LINE;
    return (
        <div className="train-board" aria-label="Aperçu du nom affiché en gare">
            <output className="train-board-name">{name}</output>
            <ul className="train-board-parts">
                <li>
                    Ligne <b>{line || "—"}</b>
                </li>
                <li>
                    Service{" "}
                    <b>
                        {isMaintenance
                            ? "Entretien"
                            : service
                              ? SERVICE_NAMES[service]
                              : "—"}
                    </b>
                </li>
                <li>
                    Numéro{" "}
                    <b>
                        {number === null
                            ? "—"
                            : String(number).padStart(2, "0")}
                    </b>
                    {numberNote && <small> {numberNote}</small>}
                </li>
            </ul>
        </div>
    );
}
