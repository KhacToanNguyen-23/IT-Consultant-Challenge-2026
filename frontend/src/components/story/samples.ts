import type { Key } from "@/client/i18n";

export type SampleOrder = { id: "contractor" | "stockout" | "traps"; title: Key; detail: Key; text: string };

/**
 * One-click demo orders. They were run against the real backend and show, in this order:
 * unit conversion with rounding up, an out-of-stock line rescued by an equal-spec alternative,
 * and lines the system must NOT guess (C18 stays C18, unknown items get no suggestion).
 */
export const SAMPLE_ORDERS: SampleOrder[] = [
  {
    id: "contractor",
    title: "story_sample_contractor_title",
    detail: "story_sample_contractor_detail",
    text: [
      "Hej, ring til Jens på +45 22 33 44 55 eller jens@bygmester.dk",
      "120 m timber 45x95 C24",
      "5 poser cement 25 kg",
      "60 m2 rockwool 95 mm",
      "10 x 4.8m timber 45x95 C24",
      "12 skivor gips 12.5 mm",
      "30 stk trykimp. terrassebræt 28x120",
    ].join("\n"),
  },
  {
    id: "stockout",
    title: "story_sample_stockout_title",
    detail: "story_sample_stockout_detail",
    text: ["10 plader gips vådrum 12.5 mm", "40 pakker isolering 95 mm", "200 sække cement 25 kg", "120 m timber 45x95 C24"].join("\n"),
  },
  {
    id: "traps",
    title: "story_sample_traps_title",
    detail: "story_sample_traps_detail",
    text: ["45x95 C18 - 30 stk", "45x95 timber", "10 stk skruer 5x50", "20 m isolering 95 mm", "blahblah ukendt ting", "5 poser cement 25 kg"].join("\n"),
  },
];
