"use client";

import { useState } from "react";

type Props = {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  isTyping?: boolean;
};

function formatSection(label: string, text: string) {
  if (!text) return null;
  return (
    <div className="mb-3">
      <span className="font-semibold text-primary-700 dark:text-primary-400 text-sm">{label}</span>
      <p className="mt-0.5 text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{text}</p>
    </div>
  );
}

function parseAssistantMessage(content: string) {
  const sections: { label: string; key: string; pattern: RegExp }[] = [
    { label: "Short Answer", key: "short_answer", pattern: /\*?\*?Short Answer\*?\*?:\s*(.*?)(?=\*?\*?Explanation|$)/s },
    { label: "Explanation", key: "explanation", pattern: /\*?\*?Explanation\*?\*?:\s*(.*?)(?=\*?\*?Relevant Law|$)/s },
    { label: "Relevant Law / Section", key: "relevant_law", pattern: /\*?\*?Relevant Law\/Section\*?\*?:\s*(.*?)(?=\*?\*?Next Steps|$)/s },
    { label: "Next Steps", key: "next_steps", pattern: /\*?\*?Next Steps\*?\*?:\s*(.*?)(?=\*?\*?Disclaimer|$)/s },
    { label: "Disclaimer", key: "disclaimer", pattern: /\*?\*?Disclaimer\*?\*?:\s*(.*?)$/s },
  ];

  const parsed: { label: string; text: string }[] = [];
  let hasStructure = false;

  for (const section of sections) {
    const match = content.match(section.pattern);
    if (match && match[1]?.trim()) {
      parsed.push({ label: section.label, text: match[1].trim() });
      hasStructure = true;
    }
  }

  return { parsed, hasStructure };
}

export default function MessageBubble({ role, content, timestamp, isTyping }: Props) {
  const [expanded, setExpanded] = useState(true);
  const isUser = role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[80%] bg-primary-600 text-white px-4 py-3 rounded-2xl rounded-br-md shadow-sm">
          <p className="text-sm leading-relaxed">{content}</p>
          {timestamp && (
            <p className="text-[10px] text-primary-200 mt-1.5 text-right">
              {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </p>
          )}
        </div>
      </div>
    );
  }

  // Assistant message
  const { parsed, hasStructure } = parseAssistantMessage(content);

  return (
    <div className="flex justify-start mb-4">
      <div className="flex gap-2.5 max-w-[85%]">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-400 flex items-center justify-center text-sm font-bold mt-1">
          ⚖
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-3 rounded-2xl rounded-tl-md shadow-sm">
          {isTyping ? (
            <div className="flex items-center gap-1 py-1">
              <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          ) : hasStructure ? (
            <div>
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 mb-2"
              >
                {expanded ? "Collapse" : "Expand"} sections
              </button>
              {expanded ? (
                parsed.map((s, i) => (
                  <div key={i}>{formatSection(s.label, s.text)}</div>
                ))
              ) : (
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                  {parsed[0]?.text || content}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{content}</p>
          )}
          {timestamp && !isTyping && (
            <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1.5">
              {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
