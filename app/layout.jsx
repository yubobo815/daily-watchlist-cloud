import "./globals.css";

export const metadata = {
  title: "Daily Watchlist",
  description: "Cloud stock and ETF watchlist powered by Supabase history."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
