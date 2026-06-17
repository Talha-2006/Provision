import Link from "next/link";

type MobileNavProps = {
  activePage?: "about" | "sources";
};

export default function MobileNav({ activePage }: MobileNavProps) {
  return (
    <details className="mobile-nav">
      <summary>Menu</summary>
      <div className="mobile-nav-menu">
        <Link
          className={activePage === "about" ? "nav-link-active" : undefined}
          href="/about"
        >
          About
        </Link>
        <Link
          className={activePage === "sources" ? "nav-link-active" : undefined}
          href="/sources"
        >
          Sources
        </Link>
      </div>
    </details>
  );
}
