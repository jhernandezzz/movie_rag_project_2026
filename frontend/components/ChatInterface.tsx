"use client";

import { useState, useEffect, useRef } from "react";
import { Clapperboard } from "lucide-react";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import { chat } from "@/lib/api";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (query: string) => {
    const userMessage: Message = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const data = await chat(query);
      const assistantMessage: Message = { role: "assistant", content: data.response };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I'm having trouble connecting to the backend. Please make sure the FastAPI server is running." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-white dark:bg-[#0a0a0a] transition-colors duration-300">
      <header className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center bg-white/80 dark:bg-[#0a0a0a]/80 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-3 max-w-7xl mx-auto w-full">
          <div className="p-2 bg-blue-600 rounded-lg text-white shadow-lg shadow-blue-500/20">
            <Clapperboard size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-gray-900 dark:text-white uppercase">
              Cinema<span className="text-blue-600">RAG</span>
            </h1>
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 tracking-widest uppercase">AI Discovery Engine</p>
          </div>
        </div>
      </header>

      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 scroll-smooth scrollbar-thin scrollbar-thumb-gray-200 dark:scrollbar-thumb-gray-800"
      >
        <div className="max-w-7xl mx-auto w-full space-y-10">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-8 opacity-70">
              <div className="p-8 bg-blue-50 dark:bg-blue-900/20 rounded-full text-6xl shadow-inner">
                🎬
              </div>
              <div className="space-y-3">
                <p className="text-gray-600 dark:text-gray-300 max-w-xl text-2xl font-medium leading-relaxed">
                  Welcome to CinemaRAG
                </p>
                <p className="text-gray-500 dark:text-gray-400 max-w-lg mx-auto text-lg">
                  Your AI-powered film discovery companion. Ask about actors, genres, or for a personalized recommendation.
                </p>
              </div>
            </div>
          )}
          {messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} />
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-8 py-4 text-sm text-gray-500 animate-pulse border border-gray-200 dark:border-gray-700 shadow-sm">
                CinemaRAG is analyzing the film archives...
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="p-8 border-t border-gray-100 dark:border-gray-800 bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto w-full">
          <ChatInput onSend={handleSendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
}
