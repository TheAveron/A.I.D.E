import { useAuthorizedImage } from "../../hooks/schematics/schematics";

type Props = {
    schematicId: number;
    hasPreview: boolean;
    title: string;
    // Changes when the preview is replaced, to load the new image
    version?: string;
};

/** The preview image of a schematic, or a placeholder. */
export default function SchematicPreview({
    schematicId,
    hasPreview,
    title,
    version,
}: Props) {
    const src = useAuthorizedImage(
        hasPreview ? `/schematics/${schematicId}/preview` : null,
        version,
    );

    if (src) {
        return (
            <img className="schematic-preview" src={src} alt={`Aperçu de ${title}`} />
        );
    }
    return (
        <div className="schematic-preview schematic-preview-empty" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 2 3 7v10l9 5 9-5V7l-9-5Z" />
                <path d="M3 7l9 5 9-5M12 12v10" />
            </svg>
            <span>{hasPreview ? "Chargement…" : "Pas d'aperçu"}</span>
        </div>
    );
}
