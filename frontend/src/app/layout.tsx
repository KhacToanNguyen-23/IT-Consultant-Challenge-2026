import "./globals.css";
import AppHeader from "@/components/AppHeader";

export const metadata = {
  title: "SiteDesk · Counter Assistant",
  description: "From raw material list to confirmed POS order — In-store counter assistant (MVP, simulated integrations)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <AppHeader />
        <main className="mx-auto max-w-[1400px] px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
