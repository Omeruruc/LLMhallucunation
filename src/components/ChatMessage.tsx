import { Bot, User, CheckCircle2, AlertCircle } from 'lucide-react';

// Kullanıcı veya ajan mesajı; ajan alanları yalnızca ajan satırında kullanılır.

interface ChatMessageProps {
  type: 'user' | 'agent';
  agentNumber?: number;
  content: string;
  color?: string;
  isThinking?: boolean;
  hasCorrected?: boolean;
}

export function ChatMessage({
  type,
  agentNumber,
  content,
  color,
  isThinking,
  hasCorrected,
}: ChatMessageProps) {
  // Kullanıcı balonu ayrı düzen; ajan balonundan önce döner.
  if (type === 'user') {
    return (
      <div className="flex items-start gap-3 mb-4">
        <div className="flex-shrink-0 w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
          <User className="w-5 h-5 text-white" />
        </div>
        {/* Avatar sabit, metin alanı esnek büyür. */}
        <div className="flex-1 bg-gray-700 text-white rounded-2xl rounded-tl-sm px-4 py-3">
          <p className="text-sm leading-relaxed">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 mb-4">
      <div
        className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
        style={{ backgroundColor: color }}
      >
        <Bot className="w-5 h-5 text-white" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-semibold text-gray-800">
            Ajan {agentNumber}
          </span>
          {hasCorrected && (
            <div className="flex items-center gap-1 text-xs text-green-600">
              <CheckCircle2 className="w-3 h-3" />
              <span>Düzeltme yaptı</span>
            </div>
          )}
          {agentNumber === 1 && (
            <div className="flex items-center gap-1 text-xs text-orange-500">
              <AlertCircle className="w-3 h-3" />
              <span>Halüsinasyon riski</span>
            </div>
          )}
        </div>
        {/* Beklerken nokta animasyonu, hazır olunca metin. */}
        <div
          className="bg-white border-2 rounded-2xl rounded-tl-sm px-4 py-3"
          style={{ borderColor: color }}
        >
          {isThinking ? (
            <div className="flex items-center gap-2 text-gray-500">
              <div className="flex gap-1">
                {/* Üç nokta için kademeli gecikme. */}
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm">Analiz ediyor...</span>
            </div>
          ) : (
            <p className="text-sm leading-relaxed text-gray-800">{content}</p>
          )}
        </div>
      </div>
    </div>
  );
}
