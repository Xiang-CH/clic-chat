import React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface CitationProps {
  title: string;
  url: string;
  className?: string;
}

export const Citation = ({ title, url, className }: CitationProps) => {
  return (
    <Link 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        className="hover:underline truncate font-medium w-56"
        title={title || url}
      >
      <div className={cn("flex items-center gap-3 text-sm bg-muted/50 p-2 rounded-lg border border-border", className)}>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          className="size-5 text-primary shrink-0"
        >
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
        </svg>
        <Link 
          href={url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="hover:underline truncate font-medium"
        >
          {title || url}
        </Link>
      </div>
    </Link>
  );
};
