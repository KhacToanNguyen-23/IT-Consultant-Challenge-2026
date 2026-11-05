import "./globals.css";
import AppHeader from "@/components/AppHeader";
import { I18nProvider } from "@/client/i18n";

export const metadata = {
  title: "SiteDesk · Counter Assistant",
  description: "From raw material list to confirmed POS order — In-store counter assistant (MVP, simulated integrations)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
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
