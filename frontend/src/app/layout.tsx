import "./globals.css";

export const metadata = {
  title: "SiteDesk — In-Store Trade Counter Assistant",
  description: "From Raw Material List to Confirmed POS Order in < 2 Minutes",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-100 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
