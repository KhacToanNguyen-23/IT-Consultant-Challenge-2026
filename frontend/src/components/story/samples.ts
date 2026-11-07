import type { Key } from "@/client/i18n";

export type SampleOrder = { id: "full" | "stockout" | "traps" | "nordic" | "email"; title: Key; detail: Key; text: string };

/**
 * One-click demo inputs. Each was run against the real backend (seeded DK catalog, simulated stock):
 * - full: the Round 1 "20-line list" moment: DA/NO mix, conversions, rounding up, three stock problems with safe alternatives
 * - stockout: an out-of-stock line rescued by an equal-spec alternative, plus a partial line
 * - traps: lines the system must NOT guess (C18 stays C18, unknown items get no suggestion)
 * - nordic: one tool, three markets (NO, SV, EN wording)
 * - email: the pre-order flow; contact details in the signature are masked
 */
export const SAMPLE_ORDERS: SampleOrder[] = [
  {
    id: "full",
    title: "story_sample_full_title",
    detail: "story_sample_full_detail",
    text: [
      "Hej Lars, her er listen fra Mikkel (tlf +45 31 22 44 66, mikkel@nordbyg.dk)",
      "120 m konstruktionstræ 45x95 C24",
      "80 m 45x70 C24",
      "10 stk lægte 45x45 C18 3,6 m",
      "15 stk 48x98 C24 4.8m",
      "60 m2 rockwool 95 mm",
      "40 m2 rockwool 145 mm",
      "24 plader gips standard 12.5 mm",
      "10 plader vådrum gips 12.5 mm",
      "10 sække cement 25 kg",
      "5 poser fliseklæb 20 kg",
      "8 poser fugemasse 5 kg",
      "40 stk terrassebræt 28x120 trykimp.",
      "8 stk terrassebræt 28x145 trykimp. 4.2m",
      "2 stk komposit terrassebræt 25x125",
      "20 stk 45x120 C24 4.8m",
      "6 sække kalkmørtel 20 kg",
      "12 m2 isolasjon 195 mm",
      "8 sekker betongblanding 25 kg",
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
  {
    id: "nordic",
    title: "story_sample_nordic_title",
    detail: "story_sample_nordic_detail",
    text: [
      "Konstruksjonsvirke 45x95 C24 - 90 meter",
      "5 säckar cement 25 kg",
      "tryckimpregnerade terrassebrädor 28x120 20 st",
      "pressure treated decking 28x145 - 12 pcs",
      "8 sekker betongblanding 25 kg",
    ].join("\n"),
  },
];

export const EMAIL_SAMPLE: SampleOrder = {
  id: "email",
  title: "story_sample_email_title",
  detail: "story_sample_email_detail",
  text: [
    "Hej,",
    "",
    "120 m konstruktionstræ 45x95 C24",
    "60 m2 rockwool 95 mm",
    "10 plader vådrum gips 12.5 mm",
    "6 sække cement 25 kg",
    "20 stk terrassebræt 28x120 trykimp. 4.2m",
    "",
    "Mvh",
    "Jens Hansen, Nordbyg ApS",
    "Tlf +45 22 33 44 55 · jens@nordbyg.dk",
  ].join("\n"),
};
