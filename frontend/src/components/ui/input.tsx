import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const fieldClass = "w-full rounded-lg border border-[var(--line-strong)] bg-white px-3 py-2.5 text-sm text-[var(--ink)] shadow-sm outline-none transition placeholder:text-slate-400 hover:border-slate-400 focus:border-[var(--primary)] focus:ring-4 focus:ring-[color:var(--primary-ring)] disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn("min-h-11", fieldClass, className)} {...props} />;
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn("min-h-36 resize-y leading-6", fieldClass, className)} {...props} />;
}
