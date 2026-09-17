import { cn } from "../utils/cn";

export function parseMask(mask: string): number[] {
  if (!mask) return [];
  return mask.split("|").map((b) => (b.trim() === "1" ? 1 : 0));
}

export function MaskRow({
  bits,
  size = "md",
  dimZeros = true,
  className,
  labels,
}: {
  bits: number[];
  size?: "sm" | "md" | "lg";
  dimZeros?: boolean;
  className?: string;
  labels?: string[];
}) {
  const cell =
    size === "lg"
      ? "w-12 h-14 text-xl"
      : size === "sm"
        ? "w-6 h-7 text-[11px]"
        : "w-9 h-11 text-base";
  return (
    <div className={cn("flex items-end gap-1.5", className)}>
      {bits.map((b, i) => (
        <div key={i} className="flex flex-col items-center gap-1.5">
          <span
            className={cn(
              "flex items-center justify-center border font-mono tabular transition-colors duration-300",
              cell,
              b === 1
                ? "border-volt/70 bg-volt/15 text-volt"
                : dimZeros
                  ? "border-line text-faint"
                  : "border-line2 text-dim"
            )}
          >
            {b}
          </span>
          {labels && (
            <span className="font-mono text-[9px] uppercase tracking-wider text-faint">
              {labels[i]}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

export function MaskText({ mask, className }: { mask: string; className?: string }) {
  return (
    <span className={cn("font-mono tabular", className)}>
      {mask.split("").map((ch, i) =>
        ch === "1" ? (
          <span key={i} className="text-volt">
            1
          </span>
        ) : ch === "0" ? (
          <span key={i} className="text-faint">
            0
          </span>
        ) : (
          <span key={i} className="text-line2">
            {ch}
          </span>
        )
      )}
    </span>
  );
}
