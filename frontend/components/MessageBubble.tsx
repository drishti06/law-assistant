"use client";

import { useState } from "react";

type Props = {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  isTyping?: boolean;
};

function renderFormattedText(text: string) {
  // Split into lines and render bullet points and bold text properly
  const lines = text.split("\n");
  return lines.map((line, i) => {
    // Process bold markers **text**
    const parts = line.split(/(\*\*.*?\*\*)/g);
    const rendered = parts.map((part, j) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={j} className="font-semibold text-gray-900 dark:text-gray-100">{part.slice(2, -2)}</strong>;
      }
      return <span key={j}>{part}</span>;
    });

    const isBullet = line.trim().startsWith("•") || line.trim().startsWith("-");
    if (isBullet) {
      return <li key={i} className="ml-1 text-sm text-gray-700 dark:text-gray-300 leading-relaxed list-none">{rendered}</li>;
    }
    if (line.trim() === "") return <div key={i} className="h-1.5" />;
    return <p key={i} className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{rendered}</p>;
  });
}

function formatSection(label: string, text: string) {
  if (!text) return null;
  return (
    <div className="mb-3">
      <span className="font-semibold text-primary-700 dark:text-primary-400 text-sm">{label}</span>
      <div className="mt-0.5">{renderFormattedText(text)}</div>
    </div>
  );
}

function parseAssistantMessage(content: string) {
  const sections: { label: string; key: string; pattern: RegExp }[] = [
    // New format
    { label: "What This Means", key: "short_answer", pattern: /\*?\*?What This Means\*?\*?:?\s*(.*?)(?=\*?\*?(?:Your Rights|Relevant Laws|What To Do)|$)/s },
    { label: "Your Rights", key: "explanation", pattern: /\*?\*?Your Rights\*?\*?:?\s*(.*?)(?=\*?\*?(?:Relevant Laws|What To Do)|$)/s },
    { label: "Relevant Laws", key: "relevant_law", pattern: /\*?\*?Relevant Laws\*?\*?:?\s*(.*?)(?=\*?\*?(?:What To Do|Get Help)|$)/s },
    { label: "What To Do Now", key: "next_steps", pattern: /\*?\*?What To Do Now\*?\*?:?\s*(.*?)(?=\*?\*?(?:Get Help|⚠️|Important)|$)/s },
    { label: "Get Help", key: "help", pattern: /\*?\*?Get Help\*?\*?:?\s*(.*?)(?=\*?\*?⚠️|⚠️|$)/s },
    // Old format (backward compat)
    { label: "Short Answer", key: "short_answer", pattern: /\*?\*?(?:Short Answer|What This Means For You)\*?\*?:?\s*(.*?)(?=\*?\*?(?:Explanation|Your Rights)|$)/s },
    { label: "Explanation", key: "explanation", pattern: /\*?\*?Explanation\*?\*?:?\s*(.*?)(?=\*?\*?Relevant Law|$)/s },
    { label: "Relevant Law / Section", key: "relevant_law", pattern: /\*?\*?Relevant Law\/Section\*?\*?:?\s*(.*?)(?=\*?\*?(?:Next Steps|What You Should)|$)/s },
    { label: "Next Steps", key: "next_steps", pattern: /\*?\*?(?:Next Steps|What You Should Do Now)\*?\*?:?\s*(.*?)(?=\*?\*?(?:Disclaimer|Where To Get|⚠️|Get Help)|$)/s },
    { label: "Where To Get Help", key: "help", pattern: /\*?\*?Where To Get Help\*?\*?:?\s*(.*?)(?=\*?\*?⚠️|⚠️|$)/s },
    { label: "Disclaimer", key: "disclaimer", pattern: /\*?\*?Disclaimer\*?\*?:?\s*(.*?)$/s },
  ];

  const parsed: { label: string; text: string }[] = [];
  const usedKeys = new Set<string>();
  let hasStructure = false;

  for (const section of sections) {
    if (usedKeys.has(section.key)) continue;
    const match = content.match(section.pattern);
    if (match && match[1]?.trim()) {
      parsed.push({ label: section.label, text: match[1].trim() });
      usedKeys.add(section.key);
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
