"use client";

import Link from "next/link";
import { useTheme } from "@/components/ThemeProvider";
import ChatWidget from "@/components/ChatWidget";

const features = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
      </svg>
    ),
    title: "AI-Powered Responses",
    desc: "Get instant, structured answers powered by advanced language models and retrieval-augmented generation.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    title: "Grounded in Real Law",
    desc: "Responses cite actual sections from IPC, CrPC, Constitution, Consumer Protection Act, IT Act, and more.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
      </svg>
    ),
    title: "Structured Format",
    desc: "Every answer includes a short answer, detailed explanation, relevant law, next steps, and a disclaimer.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.334-12.138c.896.061 1.785.147 2.666.257m-4.589 8.495a18.023 18.023 0 01-3.827-5.802" />
      </svg>
    ),
    title: "Multilingual Support",
    desc: "Ask questions in English or Hindi. Get responses in your preferred language.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
    title: "Secure & Private",
    desc: "JWT-based authentication. Your conversations are private and stored securely per user.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: "Chat History",
    desc: "All your conversations are saved. Pick up where you left off anytime.",
  },
];

const steps = [
  { num: "1", title: "Create an Account", desc: "Sign up for free in seconds with your email." },
  { num: "2", title: "Ask Your Question", desc: "Type your legal query in English or Hindi." },
  { num: "3", title: "Get Structured Answer", desc: "Receive a detailed response with citations and next steps." },
];

const laws = [
  "Indian Penal Code (IPC)",
  "Code of Criminal Procedure (CrPC)",
  "Constitution of India",
  "Consumer Protection Act",
  "Information Technology Act",
  "Hindu Marriage Act",
  "Domestic Violence Act",
  "Labour Laws & POSH Act",
];

export default function Home() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Navbar */}
      <nav className="sticky top-0 z-40 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-100 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">⚖</span>
            <span className="font-bold text-lg text-gray-900 dark:text-white">LegalBot</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              {theme === "light" ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                </svg>
              )}
            </button>
            <Link href="/login" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
              Sign In
            </Link>
            <Link href="/register" className="btn-primary text-sm px-4 py-2">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-transparent to-blue-50 dark:from-primary-950/30 dark:via-transparent dark:to-blue-950/20" />
        <div className="relative max-w-6xl mx-auto px-6 pt-20 pb-24 text-center">
          <div className="inline-flex items-center gap-2 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 text-xs font-medium px-3 py-1.5 rounded-full mb-6 border border-primary-100 dark:border-primary-800">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
            AI-Powered Legal Assistant
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
            Your Indian Law<br />
            <span className="text-primary-600 dark:text-primary-400">Assistant</span>
          </h1>

          <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-300 mb-10 max-w-2xl mx-auto leading-relaxed">
            Get instant, AI-powered answers about Indian Penal Code, Constitutional Rights,
            Consumer Protection, Cyber Law, Family Law, and more — with proper legal citations.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/register" className="btn-primary text-lg px-10 py-4 shadow-lg shadow-primary-600/25 hover:shadow-primary-600/40 transition-all">
              Start Free
            </Link>
            <a href="#features" className="border border-gray-300 dark:border-gray-600 hover:border-primary-400 text-gray-700 dark:text-gray-200 hover:text-primary-700 dark:hover:text-primary-400 font-medium py-4 px-10 rounded-lg transition-colors text-center text-lg">
              Learn More
            </a>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-3 gap-8 max-w-lg mx-auto">
            <div>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">7+</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Legal Areas</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">100+</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Law Sections</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">2</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Languages</p>
            </div>
          </div>
        </div>
      </section>

      {/* Laws covered */}
      <section className="py-12 border-y border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-center text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-6">Laws & Acts Covered</p>
          <div className="flex flex-wrap justify-center gap-3">
            {laws.map((law) => (
              <span key={law} className="text-sm px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-gray-600 dark:text-gray-300">
                {law}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Everything You Need
            </h2>
            <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
              A complete AI legal assistant built for Indian law — accurate, structured, and easy to use.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div key={f.title} className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 hover:shadow-lg hover:border-primary-200 dark:hover:border-primary-800 transition-all duration-300 group">
                <div className="w-11 h-11 rounded-xl bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  {f.icon}
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 bg-gray-50 dark:bg-gray-800/30">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              How It Works
            </h2>
            <p className="text-gray-500 dark:text-gray-400">Get legal guidance in three simple steps.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            {steps.map((s) => (
              <div key={s.num} className="text-center">
                <div className="w-12 h-12 rounded-full bg-primary-600 text-white text-lg font-bold flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-600/25">
                  {s.num}
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">{s.title}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Response preview */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-10">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Sample Response
            </h2>
            <p className="text-gray-500 dark:text-gray-400">Here&apos;s what a typical answer looks like.</p>
          </div>

          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 sm:p-8 shadow-sm">
            <div className="mb-4 inline-block bg-primary-600 text-white text-sm px-4 py-2 rounded-2xl rounded-br-md">
              What is Section 498A IPC?
            </div>
            <div className="space-y-4 ml-2">
              <div>
                <p className="text-sm font-semibold text-primary-700 dark:text-primary-400">Short Answer</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">Section 498A deals with cruelty by a husband or his relatives towards a married woman. It is a cognizable, non-bailable offence.</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-primary-700 dark:text-primary-400">Relevant Law/Section</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">Section 498A, Indian Penal Code, 1860. Punishment: imprisonment up to 3 years and fine.</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-primary-700 dark:text-primary-400">Next Steps</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">1) File an FIR at the nearest police station. 2) Consult a lawyer specializing in family/criminal law. 3) File for protection under the Domestic Violence Act, 2005.</p>
              </div>
              <div className="bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-300 text-xs px-3 py-2 rounded-lg border border-amber-200 dark:border-amber-800">
                Disclaimer: This is for educational purposes only. Consult a qualified lawyer for specific advice.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary-600 dark:bg-primary-700">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Ready to Get Legal Answers?
          </h2>
          <p className="text-primary-100 mb-8 text-lg">
            Sign up for free and start asking questions about Indian law right away.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/register" className="bg-white text-primary-700 hover:bg-primary-50 font-semibold py-3.5 px-10 rounded-lg transition-colors text-lg shadow-lg">
              Create Free Account
            </Link>
            <Link href="/login" className="border border-white/40 hover:border-white text-white font-medium py-3.5 px-10 rounded-lg transition-colors text-lg">
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 border-t border-gray-100 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-lg">⚖</span>
            <span className="font-semibold text-gray-800 dark:text-gray-200">LegalBot</span>
          </div>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            AI-powered legal assistant for Indian law. Not a substitute for professional legal advice.
          </p>
          <div className="flex gap-4 text-sm text-gray-500 dark:text-gray-400">
            <Link href="/login" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Login</Link>
            <Link href="/register" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Register</Link>
          </div>
        </div>
      </footer>

      {/* Floating Chat Widget */}
      <ChatWidget />
    </div>
  );
}
