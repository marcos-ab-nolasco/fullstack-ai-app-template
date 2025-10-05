import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  tokensUsed?: number | null;
  status?: "sending" | "sent" | "failed";
  error?: string;
  onRetry?: () => void;
  onRemove?: () => void;
}

export function MessageBubble({
  role,
  content,
  timestamp,
  tokensUsed,
  status = "sent",
  error,
  onRetry,
  onRemove,
}: MessageBubbleProps) {
  const isUser = role === "user";
  const isSystem = role === "system";
  const isFailed = status === "failed";
  const isSending = status === "sending";

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
      <div className="max-w-[80%]">
        <div
          className={cn("rounded-lg px-4 py-2 relative", {
            "bg-blue-600 text-white": isUser && !isFailed,
            "bg-red-600 text-white": isUser && isFailed,
            "bg-gray-200 text-gray-900": !isUser && !isSystem,
            "bg-yellow-100 text-yellow-900 text-sm italic": isSystem,
            "opacity-60": isSending,
          })}
        >
          {/* Sending indicator */}
          {isSending && (
            <div className="absolute -left-8 top-1/2 -translate-y-1/2">
              <svg
                className="animate-spin h-5 w-5 text-blue-600"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            </div>
          )}

          {/* Message content */}
          <div className="whitespace-pre-wrap break-words">{content}</div>

          {/* Footer with timestamp and tokens */}
          <div
            className={cn("flex items-center gap-2 mt-1 text-xs", {
              "text-blue-100": isUser && !isFailed,
              "text-red-100": isUser && isFailed,
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

            {/* Failed indicator */}
            {isFailed && (
              <>
                <span>•</span>
                <span>Falha ao enviar</span>
              </>
            )}
          </div>
        </div>

        {/* Error message and retry/remove buttons */}
        {isFailed && (
          <div className="mt-2 flex items-start gap-2 text-sm">
            {error && (
              <div className="flex-1 text-red-600 text-xs">
                <span className="font-medium">Erro:</span> {error}
              </div>
            )}
            <div className="flex gap-2">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700 transition-colors"
                >
                  Tentar novamente
                </button>
              )}
              {onRemove && (
                <button
                  onClick={onRemove}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-xs font-medium hover:bg-gray-300 transition-colors"
                >
                  Remover
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
