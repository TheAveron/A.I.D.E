import {
    useEffect,
    useId,
    useRef,
    useState,
    type PointerEvent,
    type ReactNode,
} from "react";

// Click outside to close: native where `closedby` exists, by hand elsewhere
const NATIVE_LIGHT_DISMISS =
    typeof HTMLDialogElement !== "undefined" &&
    "closedBy" in HTMLDialogElement.prototype;

function outside(event: PointerEvent<HTMLDialogElement>): boolean {
    const r = event.currentTarget.getBoundingClientRect();
    return (
        event.clientX < r.left ||
        event.clientX > r.right ||
        event.clientY < r.top ||
        event.clientY > r.bottom
    );
}

/**
 * A button that opens a form in a modal dialog. The native <dialog> keeps
 * the focus inside, closes with Esc (and a click outside), and gives the
 * focus back to the button. The form is only mounted while open, so it
 * starts empty every time.
 */
export default function FormDialog({
    label,
    title,
    children,
}: {
    label: string;
    title: string;
    children: ReactNode;
}) {
    const ref = useRef<HTMLDialogElement>(null);
    const titleId = useId();
    const [open, setOpen] = useState(false);
    const pressedOutside = useRef(false);

    // The content exists once `open` is set: then the dialog opens
    useEffect(() => {
        const dialog = ref.current;
        if (!open || !dialog || dialog.open) return;
        dialog.showModal();
        // React's autoFocus ran while the dialog was closed: showModal() then
        // focuses the close button. The first field of the form is better.
        dialog
            .querySelector<HTMLElement>(
                "form input:not([type=hidden]), form select, form textarea",
            )
            ?.focus();
    }, [open]);

    return (
        <>
            <button
                type="button"
                className="button"
                onClick={() => setOpen(true)}
            >
                {label}
            </button>
            <dialog
                ref={ref}
                className="form-dialog"
                aria-labelledby={titleId}
                // React 19 does not know the attribute yet: lowercase on purpose
                {...{ closedby: "any" }}
                onClose={() => setOpen(false)}
                onPointerDown={(e) => {
                    pressedOutside.current = !NATIVE_LIGHT_DISMISS && outside(e);
                }}
                onPointerUp={(e) => {
                    // Press and release outside: a text selection dragged out
                    // of the dialog does not close it
                    if (pressedOutside.current && outside(e)) ref.current?.close();
                    pressedOutside.current = false;
                }}
            >
                {open && (
                    <>
                        <div className="form-dialog-header">
                            <h1 id={titleId}>{title}</h1>
                            <button
                                type="button"
                                className="form-dialog-close"
                                aria-label="Fermer"
                                onClick={() => ref.current?.close()}
                            >
                                ×
                            </button>
                        </div>
                        {children}
                    </>
                )}
            </dialog>
        </>
    );
}
