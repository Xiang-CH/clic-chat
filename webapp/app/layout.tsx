import "./globals.css";
import { GeistSans } from "geist/font/sans";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { Navbar } from "@/components/navbar";
import { DevModeProvider } from "@/hooks/use-dev-mode";

export const metadata = {
  title: "CLIC CHAT",
  description:
    "AI system to community legal education",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head></head>
      <body className={cn(GeistSans.className, "antialiased dark max-h-screen overflow-hidden")}>
        <Toaster position="top-center" richColors />
        <DevModeProvider>
          <Navbar />
          {children}
        </DevModeProvider>
      </body>
    </html>
  );
}
