import { useId, useState, type KeyboardEvent } from "react";

import { useSchematicTags } from "../../hooks/schematics/schematics";
import {
    DEFAULT_TAGS,
    MAX_TAGS,
    TAG_MAX,
    cleanTag,
    isValidTag,
} from "../../utils/schematics";

type Props = {
    value: string[];
    onChange: (tags: string[]) => void;
    id?: string;
};

/**
 * Tags as removable chips. A tag is added with Enter or a comma; the tags
 * already used in the gallery (then a default list) are proposed.
 */
export default function TagInput({ value, onChange, id }: Props) {
    const listId = useId();
    const [draft, setDraft] = useState("");
    const [error, setError] = useState("");
    const { tags: used } = useSchematicTags();

    const suggestions = [
        ...used.map((t) => t.tag),
        ...DEFAULT_TAGS.filter((t) => !used.some((u) => u.tag === t)),
    ].filter((t) => !value.includes(t));

    const add = (raw: string) => {
        const tag = cleanTag(raw);
        if (!tag) return;
        if (!isValidTag(tag)) {
            setError(
                `Un tag ne contient que des lettres, chiffres, espaces et tirets (${TAG_MAX} caractères max).`,
            );
            return;
        }
        if (value.length >= MAX_TAGS && !value.includes(tag)) {
            setError(`${MAX_TAGS} tags au maximum.`);
            return;
        }
        setError("");
        if (!value.includes(tag)) onChange([...value, tag]);
        setDraft("");
    };

    const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
        if (event.key === "Enter" || event.key === ",") {
            event.preventDefault();
            add(draft);
        } else if (event.key === "Backspace" && draft === "" && value.length) {
            onChange(value.slice(0, -1));
        }
    };

    return (
        <div className="tag-input">
            {value.length > 0 && (
                <ul className="tag-list" aria-label="Tags choisis">
                    {value.map((tag) => (
                        <li key={tag} className="tag">
                            {tag}
                            <button
                                type="button"
                                className="tag-remove"
                                aria-label={`Retirer le tag ${tag}`}
                                onClick={() =>
                                    onChange(value.filter((t) => t !== tag))
                                }
                            >
                                ×
                            </button>
                        </li>
                    ))}
                </ul>
            )}
            <input
                id={id}
                type="text"
                list={listId}
                maxLength={TAG_MAX}
                autoComplete="off"
                placeholder="gare, fret… (Entrée pour ajouter)"
                value={draft}
                onChange={(e) => {
                    // A suggestion picked in the list is added at once
                    const picked = suggestions.includes(e.target.value);
                    if (picked) add(e.target.value);
                    else setDraft(e.target.value);
                }}
                onKeyDown={onKeyDown}
                onBlur={() => draft && add(draft)}
            />
            <datalist id={listId}>
                {suggestions.slice(0, 50).map((tag) => (
                    <option key={tag} value={tag} />
                ))}
            </datalist>
            {suggestions.length > 0 && (
                <div className="tag-suggestions" aria-label="Tags proposés">
                    {suggestions.slice(0, 8).map((tag) => (
                        <button
                            key={tag}
                            type="button"
                            className="tag tag-suggestion"
                            onClick={() => add(tag)}
                        >
                            + {tag}
                        </button>
                    ))}
                </div>
            )}
            {error && <small role="alert">{error}</small>}
        </div>
    );
}
