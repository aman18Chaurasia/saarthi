import type { TranscriptItem } from "@/lib/useVoiceCall";

interface TranscriptProps {
  items: TranscriptItem[];
}

export function Transcript({ items }: TranscriptProps) {
  return (
    <div className="flex flex-col gap-2 p-4 bg-muted/30 rounded-lg h-[400px] overflow-y-auto">
      {items.length === 0 && (
        <p className="text-sm text-muted-foreground text-center mt-8">
          Transcript will appear here once the call starts
        </p>
      )}

      {items.map((item, idx) => {
        if (item.type === "asr_partial") {
          return (
            <div key={idx} className="text-sm text-muted-foreground italic">
              <span className="font-semibold">Customer:</span> {item.text || "(listening...)"}
            </div>
          );
        }

        if (item.type === "asr_final") {
          return (
            <div key={idx} className="text-sm">
              <span className="font-semibold">Customer:</span> {item.text}
            </div>
          );
        }

        if (item.type === "agent_text") {
          return (
            <div key={idx} className="text-sm">
              <span className="font-semibold text-primary">Agent:</span> {item.text}
              {item.node_name && (
                <span className="ml-2 text-xs text-muted-foreground">
                  [{item.node_name}]
                </span>
              )}
            </div>
          );
        }

        return null;
      })}
    </div>
  );
}
