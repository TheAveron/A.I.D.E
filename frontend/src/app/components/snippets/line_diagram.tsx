import { Link } from "react-router";

import type { LineType } from "../../types/trains";
import LineSwatch from "./line_swatch";

const FALLBACK_COLOR = "#8a8a8a";

function safeColor(color: string | null): string {
    return /^#[0-9a-fA-F]{6}$/.test(color ?? "")
        ? (color as string)
        : FALLBACK_COLOR;
}

/**
 * One line as a metro strip: its stations in order on a coloured bar, the
 * ends bigger, and under each station the other lines that stop there.
 */
export default function LineDiagram({
    line,
    allLines,
}: {
    line: LineType;
    allLines: LineType[];
}) {
    const stops = [...line.stops].sort((a, b) => a.position - b.position);

    return (
        <div
            className="metro"
            style={
                {
                    "--metro-color": safeColor(line.color),
                } as React.CSSProperties
            }
        >
            <h3 className="metro-title">
                <Link to={`/line/${line.code}`}>
                    <LineSwatch code={line.code} color={line.color} />
                </Link>
                {line.name ? ` - ${line.name}` : ""}
            </h3>

            {stops.length < 2 ? (
                <p className="empty-state">
                    Le tracé n&apos;est pas encore défini.
                </p>
            ) : (
                <div className="metro-scroll">
                    <div className="metro-stops" role="list">
                        {stops.map(({ station }, index) => {
                            const others = allLines.filter(
                                (other) =>
                                    other.line_id !== line.line_id &&
                                    other.stops.some(
                                        (s) =>
                                            s.station.station_id ===
                                            station.station_id,
                                    ),
                            );
                            const end =
                                index === 0 || index === stops.length - 1;
                            return (
                                <div
                                    role="listitem"
                                    key={`${station.station_id}-${index}`}
                                    className={
                                        end
                                            ? "metro-stop metro-end"
                                            : "metro-stop"
                                    }
                                >
                                    <span
                                        className="metro-dot"
                                        aria-hidden="true"
                                    />
                                    <span className="metro-label">
                                        <Link
                                            to={`/station/${station.station_id}`}
                                        >
                                            {station.name}
                                        </Link>
                                        {station.dimension !== "overworld" && (
                                            <small>
                                                {station.dimension === "nether"
                                                    ? " (Nether)"
                                                    : " (End)"}
                                            </small>
                                        )}
                                    </span>
                                    {others.length > 0 && (
                                        <span
                                            className="metro-links"
                                            aria-label="Correspondances"
                                        >
                                            {others.map((other) => (
                                                <Link
                                                    key={other.line_id}
                                                    to={`/line/${other.code}`}
                                                >
                                                    <LineSwatch
                                                        code={other.code}
                                                        color={other.color}
                                                    />
                                                </Link>
                                            ))}
                                        </span>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
