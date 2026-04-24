import Link from "next/link";
import {
  Home as HomeIcon,
  User,
  Shield,
  Building2,
  Coins,
  Truck,
  Car,
  GraduationCap,
  Store,
  CreditCard,
  ArrowRight,
  Sparkles,
  Zap,
  Lock,
  Globe2
} from "lucide-react";

const products = [
  {
    id: "home_loan",
    name: "Home Loan",
    icon: HomeIcon,
    gradient: "from-blue-500 to-cyan-500",
    desc: "Build your dream home",
    live: true
  },
  {
    id: "personal_loan",
    name: "Personal Loan",
    icon: User,
    gradient: "from-green-500 to-emerald-500",
    desc: "Quick personal funding",
    live: true
  },
  {
    id: "unsecured_loan",
    name: "Unsecured Loan",
    icon: Shield,
    gradient: "from-purple-500 to-pink-500",
    desc: "No collateral needed",
    live: true
  },
  {
    id: "loan_against_property",
    name: "Loan Against Property",
    icon: Building2,
    gradient: "from-orange-500 to-red-500",
    desc: "Leverage your assets",
    live: true
  },
  {
    id: "gold_loan",
    name: "Gold Loan",
    icon: Coins,
    gradient: "from-yellow-500 to-amber-500",
    desc: "Gold-backed financing",
    live: true
  },
  {
    id: "commercial_vehicle_loan",
    name: "Commercial Vehicle",
    icon: Truck,
    gradient: "from-red-500 to-rose-500",
    desc: "Grow your business fleet",
    live: true
  },
  {
    id: "four_wheeler_loan",
    name: "Four Wheeler Loan",
    icon: Car,
    gradient: "from-indigo-500 to-blue-500",
    desc: "Own your dream car",
    live: true
  },
  {
    id: "education_loan",
    name: "Education Loan",
    icon: GraduationCap,
    gradient: "from-pink-500 to-purple-500",
    desc: "Invest in your future",
    live: true
  },
  {
    id: "msme_business_loan",
    name: "MSME Business Loan",
    icon: Store,
    gradient: "from-teal-500 to-cyan-500",
    desc: "Empower your business",
    live: true
  },
  {
    id: "credit_card",
    name: "Credit Card",
    icon: CreditCard,
    gradient: "from-cyan-500 to-blue-500",
    desc: "Smart spending companion",
    live: true
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-64 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 -right-64 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full blur-3xl" />
      </div>

      {/* Hero Section */}
      <section className="relative">
        <div className="container mx-auto px-6 py-20 md:py-32">
          <div className="text-center max-w-5xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-white text-sm font-medium mb-8 hover:bg-white/20 transition-all">
              <Sparkles className="w-4 h-4 text-yellow-400" />
              <span>AI-Powered Voice Banking Assistant</span>
              <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">LIVE</span>
            </div>

            {/* Main Heading */}
            <h1 className="text-6xl md:text-8xl font-black tracking-tight mb-6">
              <span className="bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent">
                SAARTHI
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl md:text-2xl text-slate-300 max-w-3xl mx-auto mb-4 font-light">
              Self-Adaptive AI for Responsible Tele-conversational Human Interaction
            </p>

            <p className="text-base md:text-lg text-slate-400 max-w-2xl mx-auto mb-12">
              Experience natural, multilingual voice conversations powered by advanced AI.
              Available in 10+ Indian languages with real-time compliance guardrails.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/dashboard"
                className="group relative px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold text-lg shadow-2xl hover:shadow-blue-500/50 transition-all overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                <span className="relative flex items-center justify-center gap-2">
                  View Dashboard
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </span>
              </Link>

              <a
                href="#products"
                className="px-8 py-4 bg-white/10 backdrop-blur-sm border border-white/20 text-white rounded-xl hover:bg-white/20 font-semibold text-lg transition-all"
              >
                Explore Products
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Products Grid */}
      <section id="products" className="relative container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent mb-4">
            Choose Your Product
          </h2>
          <p className="text-lg text-slate-400">
            10 BFSI products, all powered by intelligent voice AI
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 max-w-7xl mx-auto">
          {products.map((product) => {
            const Icon = product.icon;
            const isLive = product.live;

            return (
              <Link
                key={product.id}
                href={isLive ? `/call?product=${product.id}` : "#"}
                className={`group relative p-6 rounded-2xl border transition-all ${
                  isLive
                    ? "bg-white/5 backdrop-blur-sm border-white/10 hover:bg-white/10 hover:border-white/20 hover:scale-105 cursor-pointer"
                    : "bg-white/5 backdrop-blur-sm border-white/5 cursor-not-allowed opacity-40"
                }`}
              >
                {/* Live Badge */}
                {isLive && (
                  <div className="absolute top-4 right-4">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/20 border border-green-500/30 text-green-400 text-xs font-semibold">
                      <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                      LIVE
                    </span>
                  </div>
                )}

                {/* Icon */}
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${product.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-lg`}>
                  <Icon className="w-7 h-7 text-white" />
                </div>

                {/* Content */}
                <h3 className="text-lg font-bold text-white mb-2">
                  {product.name}
                </h3>

                <p className="text-sm text-slate-400 mb-4">
                  {product.desc}
                </p>

                {/* Hover Arrow */}
                {isLive && (
                  <div className="flex items-center text-blue-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    Start Demo Call
                    <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                  </div>
                )}

                {/* Gradient Border on Hover */}
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${product.gradient} opacity-0 group-hover:opacity-20 blur transition-opacity pointer-events-none`} />
              </Link>
            );
          })}
        </div>
      </section>

      {/* Features */}
      <section className="relative container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent mb-4">
            Why SAARTHI?
          </h2>
          <p className="text-lg text-slate-400">
            Built with cutting-edge AI research and real-world needs
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="group p-8 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Globe2 className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">Multilingual Support</h3>
            <p className="text-slate-400 leading-relaxed">
              Speaks 10+ Indian languages including Hindi, English, Tamil, Telugu, Marathi, Bengali, and more.
            </p>
          </div>

          <div className="group p-8 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Zap className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">Self-Learning AI</h3>
            <p className="text-slate-400 leading-relaxed">
              Continuously improves from every conversation using RLAIF and DPO training techniques.
            </p>
          </div>

          <div className="group p-8 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Lock className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">Compliance First</h3>
            <p className="text-slate-400 leading-relaxed">
              Real-time PII redaction, RBI compliance, and responsible AI guardrails built-in.
            </p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="relative container mx-auto px-6 py-16 mb-20">
        <div className="grid md:grid-cols-4 gap-8 max-w-5xl mx-auto">
          <div className="text-center p-6 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10">
            <div className="text-5xl font-black bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent mb-2">10</div>
            <div className="text-sm text-slate-400 font-medium">BFSI Products</div>
          </div>
          <div className="text-center p-6 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10">
            <div className="text-5xl font-black bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">10+</div>
            <div className="text-sm text-slate-400 font-medium">Indian Languages</div>
          </div>
          <div className="text-center p-6 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10">
            <div className="text-5xl font-black bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent mb-2">&lt;300ms</div>
            <div className="text-sm text-slate-400 font-medium">Response Time</div>
          </div>
          <div className="text-center p-6 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10">
            <div className="text-5xl font-black bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent mb-2">92%</div>
            <div className="text-sm text-slate-400 font-medium">Qualification Rate</div>
          </div>
        </div>
      </section>
    </div>
  );
}
