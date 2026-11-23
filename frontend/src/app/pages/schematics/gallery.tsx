import { Link, useSearchParams } from "react-router";

import {
    useSchematicTags,
    useSchematics,
} from "../../hooks/schematics/schematics";
import ComplianceBadge from "../../components/schematics/compliance_badge";
import SchematicPreview from "../../components/schematics/schematic_preview";
import { formatSize } from "../../utils/schematics";
import type { SchematicSummaryType } from "../../types/schematics";
import PageHeader from "../../components/common/page_header";

/** The schematics gallery. Filters live in the URL, so a view can be shared. */
export default function SchematicsGallery() {
    const [params, setParams] = useSearchParams();
    const q = params.get("q") ?? "";
    const selected = params.getAll("tag");
    const compliantOnly = params.get("conforme") === "1";

    const { schematics, loading, error } = useSchematics({
        q,
        tags: selected,
        compliantOnly,
    });
    const { tags } = useSchematicTags();

    const update = (change: (next: URLSearchParams) => void) => {
        const next = new URLSearchParams(params);
        change(next);
        setParams(next, { replace: true });
    };

    const toggleTag = (tag: string) =>
        update((next) => {
            const current = next.getAll("tag");
            next.delete("tag");
            const tagsNext = current.includes(tag)
                ? current.filter((t) => t !== tag)
                : [...current, tag];
            tagsNext.forEach((t) => next.append("tag", t));
        });

    return (
        <div className="information-container">
            <PageHeader
                title="Schematics"
                description="Les constructions partagées par les joueurs, à coller en jeu avec la Schematicannon de Create ou un bloc de structure."
                actions={
                    <Link className="button" to="/schematiques/nouveau">
                        Déposer un schematic
                    </Link>
                }
            />
            <div className="snippet-container schematics-wide">

                <div className="toolbar">
                    <input
                        type="text"
                        aria-label="Rechercher par titre"
                        placeholder="Rechercher par titre…"
                        maxLength={100}
                        value={q}
                        onChange={(e) =>
                            update((next) => {
                                if (e.target.value) {
                                    next.set("q", e.target.value);
                                } else {
                                    next.delete("q");
                                }
                            })
                        }
                    />
                    <label>
                        <input
                            type="checkbox"
                            checked={compliantOnly}
                            onChange={(e) =>
                                update((next) => {
                                    if (e.target.checked) {
                                        next.set("conforme", "1");
                                    } else {
                                        next.delete("conforme");
                                    }
                                })
                            }
                        />
                        Conformes aux normes uniquement
                    </label>
                </div>

                {(tags.length > 0 || selected.length > 0) && (
                    <div className="tag-cloud" aria-label="Filtrer par tag">
                        {[
                            ...selected.filter(
                                (t) => !tags.some((c) => c.tag === t),
                            ),
                            ...tags.map((t) => t.tag),
                        ]
                            .slice(0, 40)
                            .map((tag) => {
                                const count = tags.find(
                                    (t) => t.tag === tag,
                                )?.count;
                                const active = selected.includes(tag);
                                return (
                                    <button
                                        key={tag}
                                        type="button"
                                        className={
                                            active ? "tag tag-active" : "tag"
                                        }
                                        aria-pressed={active}
                                        onClick={() => toggleTag(tag)}
                                    >
                                        {tag}
                                        {count !== undefined && (
                                            <span className="tag-count">
                                                {count}
                                            </span>
                                        )}
                                    </button>
                                );
                            })}
                    </div>
                )}

                {error ? (
                    <p role="alert">{error}</p>
                ) : loading && schematics.length === 0 ? (
                    <p>Chargement…</p>
                ) : schematics.length === 0 ? (
                    <p className="empty-state">
                        {q || selected.length || compliantOnly
                            ? "Aucun schematic ne correspond à ces filtres."
                            : "Aucun schematic n'a encore été déposé."}
                    </p>
                ) : (
                    <ul className="schematic-grid">
                        {schematics.map((s) => (
                            <SchematicCard key={s.schematic_id} schematic={s} />
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

function SchematicCard({ schematic }: { schematic: SchematicSummaryType }) {
    const v = schematic.current;
    return (
        <li className="schematic-card">
            <Link
                to={`/schematique/${schematic.schematic_id}`}
                className="schematic-card-link"
            >
                <SchematicPreview
                    schematicId={schematic.schematic_id}
                    hasPreview={schematic.has_preview}
                    title={schematic.title}
                    version={schematic.updated_at}
                />
                <div className="schematic-card-body">
                    <h3>{schematic.title}</h3>
                    {v?.compliant && <ComplianceBadge />}
                    {v && (
                        <p className="schematic-meta">
                            {formatSize(v)} · {v.block_count.toLocaleString()}{" "}
                            blocs
                            {schematic.version_count > 1 &&
                                ` · v${v.number}`}
                        </p>
                    )}
                    <p className="schematic-meta">
                        par {schematic.author_name ?? "un ancien joueur"}
                    </p>
                    {schematic.tags.length > 0 && (
                        <ul className="tag-list">
                            {schematic.tags.map((tag) => (
                                <li key={tag} className="tag">
                                    {tag}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </Link>
        </li>
    );
}
