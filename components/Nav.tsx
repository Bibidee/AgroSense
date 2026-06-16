import Link from "next/link";
import { Brand } from "./Brand";
import { logOut } from "@/server/actions/auth";

export function Nav({ admin }: { admin?: boolean }) {
  return (
    <header className="border-b border-sage bg-ivory">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <Link href="/dashboard"><Brand /></Link>
        <nav className="hidden md:flex items-center gap-5 text-sm">
          <Link href="/dashboard" className="text-charcoal hover:text-canopy">Dashboard</Link>
          <Link href="/farms" className="text-charcoal hover:text-canopy">Farms</Link>
          <Link href="/cases/new" className="text-charcoal hover:text-canopy">New case</Link>
          <Link href="/evidence" className="text-charcoal hover:text-canopy">Evidence</Link>
          {admin && <Link href="/admin" className="text-consensus hover:underline">Admin</Link>}
          <Link href="/profile" className="text-charcoal hover:text-canopy">Profile</Link>
          <Link href="/settings" className="text-charcoal hover:text-canopy">Settings</Link>
        </nav>
        <form action={logOut}><button className="btn-ghost">Log out</button></form>
      </div>
    </header>
  );
}
