/** A coloured dot with the line's code, as on a map. */
export default function LineSwatch({
    code,
    color,
}: {
    code: string;
    color: string | null;
}) {
    return (
        <span>
            <span
                className="train-line-swatch"
                style={{ background: color ?? "var(--text-500)" }}
                aria-hidden="true"
            />
            {code}
        </span>
    );
}
