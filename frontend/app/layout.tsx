import "./globals.css";

export const metadata = { title: "Video RAG Compare", description: "Compare YouTube and Instagram Reels" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
