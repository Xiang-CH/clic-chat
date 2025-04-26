"use client";

import type { Message } from "ai";
import { motion } from "framer-motion";

import { SparklesIcon } from "./icons";
import { Markdown } from "./markdown";
import { PreviewAttachment } from "./preview-attachment";
import { cn } from "@/lib/utils";
import { Weather } from "./weather";
import { Citation } from "./citation";
import { Groundings } from "./groundings-display";
import { ScrollArea } from "./ui/scroll-area";

export const PreviewMessage = ({
  message,
  chatId,
  isLoading,
  groundings,
}: {
  chatId: string;
  message: Message;
  isLoading: boolean;
  groundings?: Groundings;
}) => {
  if (!message.content) return null;
  
  // URL regex pattern
  const urlRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
  let urlsInContent: {url: string, title: string}[] = [];
  
  if (message.role === "assistant" && typeof message.content === "string") {
    const matches = [...message.content.matchAll(urlRegex)];
    urlsInContent = matches.map(match => ({
      title: match[1],
      url: match[2]
    }));
  }
  
  // Find matching titles from groundings if available
  const findTitleForUrl = (url: string) => {
    if (!groundings) return "";
    
    // Check ordinances
    if (groundings.ordinances) {
      const match = groundings.ordinances.find((ord: any) => ord.url === url);
      if (match) return `Cap ${match.cap_no}, Section ${match.section_no}`;
    }
    
    // Check judgements
    if (groundings.judgements) {
      const match = groundings.judgements.find((judge: any) => judge.url === url);
      if (match) return match.case_name;
    }
    
    return "";
  };

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      data-role={message.role}
    >
      <div
        className={cn(
          "group-data-[role=user]/message:bg-primary group-data-[role=user]/message:text-primary-foreground flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl",
        )}
      >
        {message.role === "assistant" && message.content && (
          <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
            <SparklesIcon size={14} />
          </div>
        )}

        <div className="flex flex-col gap-2 w-full">
          {message.role === "user" && message.content && (
            <div className="flex flex-col gap-4">
              <Markdown>{message.content as string}</Markdown>
            </div>
          )}

          {message.role === "assistant" && message.content && 
          
              message.parts?.map((part, index) => {
                if (part.type === "text") {
                  return <Markdown key={index}>{part.text}</Markdown>;
                } else if (part.type === "source") {
                  return <Citation key={index} title={part.source.title || ""} url={part.source.url} />;
                }
                return null;
              })
          }

          {message.role === "assistant" && urlsInContent && 
                <div className="flex gap-2 w-full max-w-full flex-wrap">
            {urlsInContent.map((citation, index) => (
              <Citation key={index} title={citation.title} url={citation.url} />
            ))}
                </div>
          }

          {message.experimental_attachments && (
            <div className="flex flex-row gap-2 space-y-1">
              {message.experimental_attachments.map((attachment) => (
                <PreviewAttachment
                  key={attachment.url}
                  attachment={attachment}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export const ThinkingMessage = ({ query }: { query: string | null | undefined }) => {
  const role = "assistant";

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message "
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1, transition: { delay: 1 } }}
      data-role={role}
    >
      <div
        className={cn(
          "flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl",
          {
            "group-data-[role=user]/message:bg-muted": true,
          },
        )}
      >
        <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
          <SparklesIcon size={14} />
        </div>

        <div className="flex flex-col gap-2 w-full">
          <div className="flex flex-col text-muted-foreground">
            {query ? (
              <motion.span
                initial={{ opacity: 0.2 }}
                animate={{ opacity: [0.2, 1, 0.2] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                Searching for: {query}
              </motion.span>
            ) : (
              <motion.span
                initial={{ opacity: 0.2 }}
                animate={{ opacity: [0.2, 1, 0.2] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                Thinking...
              </motion.span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
