import { Link } from "react-router";

import SectionIcon from "../components/common/section_icon";

import { usePublicStats } from "../hooks/common/public_stats";
import { usePublicLines } from "../hooks/network/map";
import { useAuth } from "../utils/authcontext";
import { NAV_SECTIONS, visibleItems } from "../utils/navigation";
import type { LineType } from "../types/trains";

/** What each section is for, in one line. */
const SECTION_INTROS: Record<string, string> = {
    economie: "Les factions, leurs monnaies et les échanges entre joueurs.",
    reseau: "Le chemin de fer : plan, lignes, gares et trains.",
    ressources: "La documentation du serveur, les schematics et les archives.",
};

// Used when the network has no line yet: the drawing still has its colors
const FALLBACK_COLORS = ["#e8891c", "#6b8bff", "#3fc6b4", "#d1362a"];

/** Black or white, whichever reads better on `hex`. */
function textOn(hex: string): string {
    const m = /^#?([0-9a-f]{6})$/i.exec(hex);
    if (!m) return "#fff";
    const n = parseInt(m[1], 16);
    const [r, g, b] = [n >> 16, (n >> 8) & 255, n & 255];
    return 0.299 * r + 0.587 * g + 0.114 * b > 150 ? "#111" : "#fff";
}

/**
 * A metro diagram of the real network (its first four lines, their colors and
 * number of stations), drawn as decoration. A small train runs once along the
 * first line.
 */
function RailwayArt({ lines }: { lines: LineType[] }) {
    // The real lines in color; up to four rows, the rest drawn as dashed
    // "lines to come" (all four in color while nothing is loaded)
    const real = lines.slice(0, 4).map((l) => ({
        code: l.code,
        color: l.color,
        stops: l.stops.length,
        planned: false,
    }));
    const shown = [
        ...real,
        ...FALLBACK_COLORS.slice(real.length).map((color, i) => ({
            code: "",
            color: real.length ? null : color,
            stops: 3 + i,
            planned: real.length > 0,
        })),
    ];

    return (
        <svg
            className="home-railway"
            viewBox="0 0 480 280"
            aria-hidden="true"
            focusable="false"
        >
            {shown.map((line, i) => {
                const color = line.planned
                    ? "var(--border-strong)"
                    : line.color || FALLBACK_COLORS[i % 4];
                const y = 40 + i * 66;
                // Lines bend up or down in the middle, like a metro map
                const d = i === 0 ? 0 : i % 2 ? 26 : -26;
                const path = `M 44 ${y} H 150 L 180 ${y + d} H 300 L 330 ${y} H 468`;
                // Stations sit on the straight parts
                const slots = [80, 125, 205, 250, 290, 360, 410, 455];
                const count = Math.min(Math.max(line.stops, 2), 8);
                const xs = slots
                    .filter((_, k) => k % Math.ceil(8 / count) === 0)
                    .slice(0, count);
                const yAt = (x: number) =>
                    x > 180 && x < 300 ? y + d : y;
                return (
                    <g
                        key={i}
                        className={
                            line.planned
                                ? "home-railway-line home-railway-planned"
                                : "home-railway-line"
                        }
                    >
                        <path d={path} stroke={color} />
                        {xs.map((x) => (
                            <circle
                                key={x}
                                className="home-railway-station"
                                cx={x}
                                cy={yAt(x)}
                                r="6"
                                stroke={color}
                            />
                        ))}
                        <rect
                            x="6"
                            y={y - 15}
                            width="30"
                            height="30"
                            rx="6"
                            fill={line.planned ? "none" : color}
                            stroke={line.planned ? color : undefined}
                            strokeDasharray={line.planned ? "4 4" : undefined}
                        />
                        {line.code && (
                            <text
                                x="21"
                                y={y + 5.5}
                                textAnchor="middle"
                                fill={textOn(color)}
                            >
                                {line.code}
                            </text>
                        )}
                    </g>
                );
            })}
            <g className="home-railway-train">
                <rect x="-4" y="31" width="34" height="18" rx="5" />
                <rect x="2" y="35" width="7" height="6" rx="1.5" />
                <rect x="12" y="35" width="7" height="6" rx="1.5" />
            </g>
        </svg>
    );
}

/** The home page: what the site is, the network at a glance, its sections. */
function Home() {
    const { token } = useAuth();
    const loggedIn = !!token;
    const { lines } = usePublicLines();
    const stats = usePublicStats();

    return (
        <div className="home">
            <section className="home-hero" aria-labelledby="home-title">
                <div className="home-hero-text">
                    <p className="home-eyebrow">
                        <span className="home-block" aria-hidden="true" />
                        Serveur Minecraft · saison actuelle
                    </p>
                    <h1 id="home-title">
                        Cube Crusader
                        <span>Age of Steam</span>
                    </h1>
                    <p className="home-lead">
                        Fondez une faction, frappez votre monnaie, commercez avec
                        les autres joueurs et reliez vos villes par le rail. Ce
                        site accompagne le serveur : la carte en direct, le
                        marché, le réseau ferré et toute la documentation.
                    </p>
                    <div className="home-actions">
                        <Link className="button" to="/actual">
                            Ouvrir la carte
                        </Link>
                        <Link className="button home-button-ghost" to="/network">
                            Plan du réseau
                        </Link>
                        {!loggedIn && (
                            <Link className="home-login" to="/login">
                                Se connecter pour tout voir →
                            </Link>
                        )}
                    </div>
                </div>
                <RailwayArt lines={lines} />
            </section>

            {stats && (
                <dl className="home-stats">
                    <div>
                        <dt>Joueurs inscrits</dt>
                        <dd>{stats.members.toLocaleString()}</dd>
                    </div>
                    <div>
                        <dt>Projets sur la carte</dt>
                        <dd>{stats.projects.toLocaleString()}</dd>
                    </div>
                    {lines.length > 0 && (
                        <div className="home-stats-lines">
                            <dt>Le réseau</dt>
                            <dd>
                                {lines.slice(0, 12).map((l) => (
                                    <span
                                        key={l.code}
                                        className="home-line-chip"
                                        style={{
                                            backgroundColor: l.color ?? undefined,
                                            color: l.color
                                                ? textOn(l.color)
                                                : undefined,
                                        }}
                                        title={l.name ?? `Ligne ${l.code}`}
                                    >
                                        {l.code}
                                    </span>
                                ))}
                            </dd>
                        </div>
                    )}
                </dl>
            )}

            <div className="home-sections">
                {NAV_SECTIONS.map((section) => {
                    const items = visibleItems(section, loggedIn);
                    if (items.length === 0) return null;
                    return (
                        <article
                            key={section.id}
                            className={`home-card home-card-${section.id}`}
                        >
                            <SectionIcon
                                section={section.id}
                                className="home-card-icon"
                            />
                            <h2>{section.label}</h2>
                            <p>{SECTION_INTROS[section.id]}</p>
                            <ul>
                                {items.map((item) => (
                                    <li key={item.to}>
                                        <Link to={item.to}>{item.label}</Link>
                                    </li>
                                ))}
                            </ul>
                        </article>
                    );
                })}
            </div>
        </div>
    );
}

export default Home;
