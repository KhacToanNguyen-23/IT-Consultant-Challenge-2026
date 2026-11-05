import "./globals.css";
import { Barlow, Barlow_Condensed, IBM_Plex_Mono, VT323 } from "next/font/google";
import AppHeader from "@/components/AppHeader";
import { I18nProvider } from "@/client/i18n";

// All four carry the Vietnamese subset; latin-ext covers Danish (æ, ø, å). next/font needs literal options.
const barlow = Barlow({ subsets: ["latin", "latin-ext", "vietnamese"], weight: ["400", "500", "600", "700"], variable: "--font-barlow", display: "swap" });
const barlowCondensed = Barlow_Condensed({ subsets: ["latin", "latin-ext", "vietnamese"], weight: ["500", "600", "700"], variable: "--font-barlow-condensed", display: "swap" });
const plexMono = IBM_Plex_Mono({ subsets: ["latin", "latin-ext", "vietnamese"], weight: ["400", "600"], variable: "--font-plex-mono", display: "swap" });
const vt323 = VT323({ subsets: ["latin", "latin-ext", "vietnamese"], weight: "400", variable: "--font-vt323", display: "swap" });

export const metadata = {
  title: "SiteDesk · Counter Assistant",
  description: "From raw material list to confirmed POS order — In-store counter assistant (MVP, simulated integrations)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${barlow.variable} ${barlowCondensed.variable} ${plexMono.variable} ${vt323.variable}`}>
      <body className="antialiased">
        <I18nProvider>
          <div className="pos-shell">
            <AppHeader />
            <main className="pos-main">{children}</main>
          </div>
        </I18nProvider>
      </body>
    </html>
  );
}
