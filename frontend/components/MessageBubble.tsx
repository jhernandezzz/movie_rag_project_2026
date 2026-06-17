import ReactMarkdown from "react-markdown";
import { Message } from "./ChatInterface";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex w-full mb-8", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[90%] md:max-w-[85%] rounded-3xl px-8 py-6 shadow-sm transition-all duration-200",
          isUser
            ? "bg-blue-600 text-white rounded-tr-none hover:bg-blue-700 shadow-blue-500/10"
            : "bg-white text-gray-800 dark:bg-gray-800 dark:text-gray-100 rounded-tl-none border border-gray-100 dark:border-gray-700 shadow-gray-200/50 dark:shadow-none"
        )}
      >
        {isUser ? (
          <p className="text-[17px] leading-relaxed font-semibold">{message.content}</p>
        ) : (
          <div className="prose dark:prose-invert max-w-none 
            prose-p:leading-9 prose-p:mb-6 last:prose-p:mb-0
            prose-headings:font-black prose-headings:text-gray-900 dark:prose-headings:text-white prose-headings:mb-4
            prose-strong:text-blue-600 dark:prose-strong:text-blue-400 prose-strong:font-black
            prose-ul:list-disc prose-ul:pl-8 prose-ul:mb-6 prose-ul:space-y-3
            prose-li:pl-2
            prose-ol:list-decimal prose-ol:pl-8 prose-ol:mb-6 prose-ol:space-y-3
            text-[17px]">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
