import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  tokensUsed?: number | null;
}

export function MessageBubble({ role, content, timestamp, tokensUsed }: MessageBubbleProps) {
  const isUser = role === "user";
  const isSystem = role === "system";

  // Format timestamp to relative or absolute
  const formatTimestamp = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "agora";
    if (diffMins < 60) return `há ${diffMins}m`;
    if (diffHours < 24) return `há ${diffHours}h`;
    if (diffDays < 7) return `há ${diffDays}d`;

    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div
      className={cn("flex w-full mb-4", {
        "justify-end": isUser,
        "justify-start": !isUser,
        "justify-center": isSystem,
      })}
    >
      <div
        className={cn("max-w-[80%] rounded-lg px-4 py-2", {
          "bg-blue-600 text-white": isUser,
          "bg-gray-200 text-gray-900": !isUser && !isSystem,
          "bg-yellow-100 text-yellow-900 text-sm italic": isSystem,
        })}
      >
        {/* Message content */}
        <div className="whitespace-pre-wrap break-words">{content}</div>

        {/* Footer with timestamp and tokens */}
        <div
          className={cn("flex items-center gap-2 mt-1 text-xs", {
            "text-blue-100": isUser,
            "text-gray-600": !isUser && !isSystem,
            "text-yellow-700": isSystem,
          })}
        >
          <span>{formatTimestamp(timestamp)}</span>

          {/* Tokens badge (only for assistant messages) */}
          {!isUser && !isSystem && tokensUsed !== null && tokensUsed !== undefined && (
            <>
              <span>•</span>
              <span className="font-mono">{tokensUsed} tokens</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
