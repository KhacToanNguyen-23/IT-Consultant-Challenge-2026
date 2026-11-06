"use client";

import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export default function ListPagination({ total, page, pageSize, onPageChange }: Props) {
  const navRef = useRef<HTMLElement>(null);
  const changePage = (nextPage: number) => {
    const feed = navRef.current?.closest(".pos-feed");
    if (feed && feed.scrollHeight > feed.clientHeight + 1) feed.scrollTo({ top: 0, behavior: "auto" });
    else window.scrollTo({ top: 0, behavior: "auto" });
    onPageChange(nextPage);
  };
  const pages = Math.ceil(total / pageSize);
  if (pages <= 1) return null;

  const first = page * pageSize + 1;
  const last = Math.min(total, first + pageSize - 1);

  return (
    <nav ref={navRef} className="list-pagination" aria-label="List pagination">
      <span className="text-xs font-medium tabular text-slate-600" aria-live="polite">{first}-{last} of {total}</span>
      <div className="list-pagination-controls">
        <button type="button" className="key key--sm key--nav !min-h-9 !flex-row !gap-1" aria-label="Previous page" disabled={page === 0} onClick={() => changePage(page - 1)}>
          <ChevronLeft size={15} aria-hidden /> <span className="list-pagination-label">Previous</span>
        </button>
        <button type="button" className="key key--sm key--nav !min-h-9 !flex-row !gap-1" aria-label="Next page" disabled={page >= pages - 1} onClick={() => changePage(page + 1)}>
          <span className="list-pagination-label">Next</span> <ChevronRight size={15} aria-hidden />
        </button>
      </div>
    </nav>
  );
}