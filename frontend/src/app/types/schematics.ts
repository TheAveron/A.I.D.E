export interface SchematicVersionType {
    number: number;
    original_name: string;
    size_bytes: number;
    sha256: string;
    size_x: number;
    size_y: number;
    size_z: number;
    // Blocks that are not air
    block_count: number;
    data_version: number | null;
    comment: string | null;
    uploaded_by_user_id: number | null;
    uploaded_by_name: string | null;
    uploaded_at: string;
    // Checked against the railway standards by a train admin
    compliant: boolean;
    compliant_at: string | null;
}

/** A card of the gallery. */
export interface SchematicSummaryType {
    schematic_id: number;
    title: string;
    tags: string[];
    author_user_id: number | null;
    author_name: string | null;
    has_preview: boolean;
    created_at: string;
    updated_at: string;
    version_count: number;
    current: SchematicVersionType | null;
}

export interface SchematicType extends SchematicSummaryType {
    description: string | null;
    // Newest first
    versions: SchematicVersionType[];
    can_edit: boolean;
    can_review: boolean;
}

export interface TagCountType {
    tag: string;
    count: number;
}

export interface SchematicFilters {
    q?: string;
    tags?: string[];
    compliantOnly?: boolean;
    authorUserId?: number;
}
