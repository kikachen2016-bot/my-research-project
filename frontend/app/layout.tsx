import './globals.css';
import Link from 'next/link';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Interview BARS System',
  description: '外国人ITエンジニア面談力診断システム',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <header className="topbar">
          <div className="topbar-inner">
            <Link className="brand" href="/">Interview BARS System</Link>
            <nav>
              <Link href="/">ホーム</Link>
              <Link href="/preparation">面談準備</Link>
              <Link href="/session/new">面談診断</Link>
              <Link href="/history">履歴</Link>
              <Link href="/criteria">評価基準</Link>
            </nav>
          </div>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
