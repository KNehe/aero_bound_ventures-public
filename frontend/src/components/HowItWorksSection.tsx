import {
  FaRegCheckCircle,
  FaRegPaperPlane,
  FaRegSmile,
  FaRegStar,
} from "react-icons/fa";
import { HiOutlineSparkles } from "react-icons/hi2";

const steps = [
  {
    number: "01",
    title: "Tell Us Where You Want To Go",
    desc: "Share your route, dates, budget, and any travel preferences in a quick form or chat.",
    icon: <FaRegPaperPlane className="h-5 w-5" />,
    accent: "from-sky-500 to-cyan-400",
  },
  {
    number: "02",
    title: "Review Curated Flight Options",
    desc: "We surface smart options with the right balance of price, timing, baggage, and convenience.",
    icon: <HiOutlineSparkles className="h-5 w-5" />,
    accent: "from-blue-600 to-sky-500",
  },
  {
    number: "03",
    title: "Approve And Confirm",
    desc: "Choose the itinerary that fits best. We guide you through payment and lock it in fast.",
    icon: <FaRegCheckCircle className="h-5 w-5" />,
    accent: "from-cyan-500 to-teal-400",
  },
  {
    number: "04",
    title: "Travel With Confidence",
    desc: "Receive timely updates, responsive support, and a smoother trip from takeoff to arrival.",
    icon: <FaRegSmile className="h-5 w-5" />,
    accent: "from-sky-400 to-blue-500",
  },
];

const highlights = [
  "Human support, not just search results",
  "Tailored options for business, family, or solo travel",
  "Fast booking flow with clear next steps",
];

export default function HowItWorksSection() {
  return (
    <section className="relative isolate overflow-hidden bg-[linear-gradient(180deg,#f8fcff_0%,#eef7ff_52%,#ffffff_100%)] px-4 py-20 md:px-0">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-12 h-72 w-72 -translate-x-[140%] rounded-full bg-sky-200/50 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-0 top-24 h-80 w-80 translate-x-1/3 rounded-full bg-blue-100/80 blur-3xl"
      />

      <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.92fr_1.08fr] lg:items-start">
        <div className="relative rounded-[2rem] border border-white/70 bg-white/80 p-8 shadow-[0_18px_60px_rgba(15,23,42,0.08)] ring-1 ring-sky-100/80 backdrop-blur xl:p-10">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-sky-800">
            <FaRegStar className="h-3.5 w-3.5" />
            How It Works
          </div>

          <h2 className="max-w-md text-3xl font-black tracking-[-0.04em] text-slate-950 md:text-5xl">
            Booking flights should feel calm, clear, and personal.
          </h2>

          <p className="mt-5 max-w-xl text-base leading-7 text-slate-600 md:text-lg">
            Aero Bound Ventures combines travel expertise with a lightweight booking experience,
            so you spend less time comparing tabs and more time preparing for the trip.
          </p>

          <div className="mt-8 space-y-3">
            {highlights.map((highlight) => (
              <div
                key={highlight}
                className="flex items-start gap-3 rounded-2xl border border-slate-100 bg-slate-50/80 px-4 py-3"
              >
                <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-100 text-sky-700">
                  <FaRegCheckCircle className="h-3.5 w-3.5" />
                </span>
                <p className="text-sm font-medium text-slate-700 md:text-[0.95rem]">{highlight}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <div className="rounded-2xl bg-slate-950 px-4 py-3 text-white shadow-lg">
              <div className="text-2xl font-black tracking-[-0.04em]">4 steps</div>
              <div className="text-sm text-sky-100">From request to takeoff</div>
            </div>
            <div className="rounded-2xl border border-sky-100 bg-white px-4 py-3 text-slate-700 shadow-sm">
              <div className="text-2xl font-black tracking-[-0.04em] text-sky-800">1:1 support</div>
              <div className="text-sm text-slate-500">Guidance when you need it</div>
            </div>
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          {steps.map((step, index) => (
            <article
              key={step.number}
              className={`group relative overflow-hidden rounded-[1.75rem] border border-white/80 bg-white/88 p-6 shadow-[0_16px_45px_rgba(14,23,42,0.08)] ring-1 ring-slate-100/80 transition-transform duration-300 hover:-translate-y-1 ${
                index % 2 === 1 ? "md:translate-y-10" : ""
              }`}
            >
              <div
                aria-hidden="true"
                className={`absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r ${step.accent}`}
              />
              <div className="flex items-start justify-between gap-4">
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg">
                  {step.icon}
                </div>
                <span className="text-sm font-black tracking-[0.22em] text-sky-200">
                  {step.number}
                </span>
              </div>

              <h3 className="mt-6 max-w-xs text-xl font-bold tracking-[-0.03em] text-slate-900">
                {step.title}
              </h3>
              <p className="mt-3 text-sm leading-7 text-slate-600 md:text-[0.96rem]">
                {step.desc}
              </p>

              <div className="mt-6 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-sky-700">
                <span className="h-1.5 w-1.5 rounded-full bg-sky-500" />
                Step {step.number}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
