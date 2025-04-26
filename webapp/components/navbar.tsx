"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";

import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "./ui/navigation-menu"
import { cn } from "@/lib/utils";
import { useDevMode } from "@/hooks/use-dev-mode";

export const Navbar = () => {
  const pathname = usePathname();
  const { isDevMode, toggleDevMode } = useDevMode();

  return (
    <NavigationMenu className="max-w-full w-full justify-between px-4 py-2 border-b gap-4 box-border">
      <div className="flex items-center">
        <NavigationMenuList>
          <NavigationMenuItem>
            <Link href="/" legacyBehavior passHref>
              <NavigationMenuLink className="font-medium text-lg">
                CLIC CHAT
              </NavigationMenuLink>
            </Link>
          </NavigationMenuItem>
        </NavigationMenuList>
        
        <NavigationMenuList className="ml-4">
          <NavigationMenuItem>
            <Link href="/search" legacyBehavior passHref>
              <NavigationMenuLink 
                className={cn(
                  "group inline-flex h-9 w-max items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50",
                  pathname === "/search" && "underline underline-offset-4 border-primary"
                )}
              >
                Search
              </NavigationMenuLink>
            </Link>
          </NavigationMenuItem>
          
          <NavigationMenuItem>
            <Link href="/consult" legacyBehavior passHref>
              <NavigationMenuLink 
                className={cn(
                  "group inline-flex h-9 w-max items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50",
                  pathname === "/consult" && "underline underline-offset-4 border-primary"
                )}
              >
                Consult
              </NavigationMenuLink>
            </Link>
          </NavigationMenuItem>
        </NavigationMenuList>
      </div>

      <div className="hidden md:flex items-center space-x-2">
        <Label htmlFor="dev-mode" className="text-sm">Dev Mode</Label>
        <Switch
          id="dev-mode"
          checked={isDevMode}
          onCheckedChange={toggleDevMode}
        />
      </div>
    </NavigationMenu>
  );
};
