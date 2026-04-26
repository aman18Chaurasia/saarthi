# SAARTHI UI Redesign - Design Mockups

Modern, professional interface for AI voice agent platform.

---

## Design Principles

- **Glassmorphism**: Frosted glass cards with backdrop blur
- **Gradient accents**: Blue → Violet brand gradient
- **Micro-interactions**: Smooth animations on hover/click
- **Dark theme**: Slate-900 base with white/10 overlays
- **Responsive**: Mobile-first, scales to desktop

---

## 1. Call Page Redesign

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  ← SAARTHI          Personal Loan          🌐 Hindi    ⚙️   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │  CALL        │  │  LIVE TRANSCRIPT                    │  │
│  │  CONTROL     │  │  ┌──────────────────────────────┐  │  │
│  │              │  │  │ 🔴 Recording • 2:34           │  │  │
│  │  [AVATAR]    │  │  └──────────────────────────────┘  │  │
│  │   Priya      │  │                                     │  │
│  │              │  │  ┌───────────────────────┐         │  │
│  │  🎤 Active   │  │  │ Agent: "Welcome to... │ ←Glass │  │
│  │              │  │  └───────────────────────┘  card   │  │
│  │  ┌────────┐  │  │                                     │  │
│  │  │  END   │  │  │         ┌────────────────┐         │  │
│  │  │  CALL  │  │  │         │ You: "Interest │ ←Glass │  │
│  │  └────────┘  │  │         │      rate?"     │  card  │  │
│  │              │  │         └────────────────┘         │  │
│  │  STATS       │  │                                     │  │
│  │  Turns: 8    │  │  [Auto-scroll to bottom]           │  │
│  │  Latency:    │  │                                     │  │
│  │   ASR: 120ms │  │  ┌──────────────────────┐         │  │
│  │   LLM: 340ms │  │  │ 📝 Type contact info  │         │  │
│  │              │  │  │ [___________________] │         │  │
│  │  Call ID:    │  │  │ [Send →]              │         │  │
│  │  call_123... │  │  └──────────────────────┘         │  │
│  │  [📋 Copy]   │  │                                     │  │
│  └──────────────┘  └────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  💡 AGENT ASSISTS (2)                               │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ 🎯 Interest Rate Details        [Confidence: │  │   │
│  │  │                                   ████░ 85%]  │  │   │
│  │  │ "Our Personal Loan rates start from 10.5%    │  │   │
│  │  │  p.a. for salaried customers..."             │  │   │
│  │  │                                               │  │   │
│  │  │ Context: "interest rate percentage"          │  │   │
│  │  │ [✓ Used This] [👍] [👎]                      │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Visual Features

**Call Control Card (Left)**
- Glassmorphism: `bg-white/5 backdrop-blur-xl border-white/10`
- Animated avatar with pulse ring when speaking
- Large red "END CALL" button with glow effect
- Stats with icon badges (🔊 ASR, 🧠 LLM, 🔊 TTS)
- Monospace font for Call ID

**Transcript Area (Center-Right)**
- Full-height scrollable area
- Agent messages: Blue gradient glass cards, left-aligned
- User messages: Green gradient glass cards, right-aligned
- Typing indicator with animated dots
- Auto-scroll with smooth animation

**Nudge Panel (Bottom)**
- Collapsible panel, slides up from bottom
- Badge count on header: "💡 Agent Assists (2)"
- Cards with priority color accents:
  - High: Red/pink glow
  - Medium: Yellow/amber glow
  - Low: Blue glow
- Confidence bar visualization
- Quick action buttons with haptic feedback

### Animations

- Transcript messages: Slide in from side with fade
- Nudges: Slide up from bottom with bounce
- Stats: Count-up animation when values change
- Button hover: Scale 1.05 + glow increase

---

## 2. NudgePanel Component Redesign

### Card Layout

```
┌──────────────────────────────────────────────────────┐
│  💡 AGENT ASSISTS                    [Minimize ▼]    │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ 🔴 HIGH PRIORITY                              │  │
│  │ ╔═══════════════════════════════════════════╗ │  │
│  │ ║ 🎯 Handle Rate Objection                  ║ │  │
│  │ ║                         [Confidence 92%] ║ │  │
│  │ ╠═══════════════════════════════════════════╣ │  │
│  │ ║ "Our rates are competitive compared to   ║ │  │
│  │ ║  market. Plus, special discounts for     ║ │  │
│  │ ║  existing customers and high CIBIL..."   ║ │  │
│  │ ╠═══════════════════════════════════════════╣ │  │
│  │ ║ 💬 Triggered by: "expensive costly"      ║ │  │
│  │ ╚═══════════════════════════════════════════╝ │  │
│  │                                               │  │
│  │ [✓ Used This]  [👍 Helpful]  [👎 Not]  [✕]  │  │
│  └───────────────────────────────────────────────┘  │
│                                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ 🟡 MEDIUM PRIORITY                            │  │
│  │ ┌─────────────────────────────────────────┐  │  │
│  │ │ 📄 Documentation Required    [Conf 78%] │  │  │
│  │ │ "For Personal Loan: PAN, Aadhaar..."    │  │  │
│  │ │ 💬 Triggered by: "documents required"   │  │  │
│  │ └─────────────────────────────────────────┘  │  │
│  │ [Actions...]                                  │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Visual Features

- **Priority-based styling:**
  - High: `border-red-500/50 bg-red-500/10 shadow-[0_0_20px_rgba(239,68,68,0.3)]`
  - Medium: `border-yellow-500/50 bg-yellow-500/10`
  - Low: `border-blue-500/50 bg-blue-500/10`

- **Card states:**
  - Fresh: Pulse animation
  - Viewed: Opacity 90%
  - Used: Green checkmark badge
  - Dismissed: Slide out animation

- **Interactive elements:**
  - Confidence bar: Gradient fill animation
  - Buttons: Hover scale + color shift
  - Dismiss: Swipe gesture support

---

## 3. Dashboard Redesign

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  SAARTHI Dashboard                         Profile [Aman] ⚙️│
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ 📞 245  │  │ ✅ 189  │  │ ⏱️ 4.2m │  │ 🎯 77%  │       │
│  │ Calls   │  │ Success │  │ Avg     │  │ Success │       │
│  │ ↑ 12%   │  │ Today   │  │ Time    │  │ Rate    │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                               │
│  ┌──────────────────────────┐  ┌──────────────────────────┐│
│  │  📊 Call Volume          │  │  💡 Nudge Effectiveness  ││
│  │  ┌─────────────────────┐ │  │  ┌─────────────────────┐││
│  │  │    /\      /\        │ │  │  │ Viewed: 85%         │││
│  │  │   /  \    /  \    /\ │ │  │  │ Used: 62%           │││
│  │  │  /    \  /    \  /  \│ │  │  │ Helpful: 91%        │││
│  │  │─────────────────────│ │  │  │                     │││
│  │  │ Mon  Tue  Wed  Thu   │ │  │  │ [Donut Chart]       │││
│  │  └─────────────────────┘ │  │  └─────────────────────┘││
│  └──────────────────────────┘  └──────────────────────────┘│
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  📋 Recent Calls                        [View All →]    ││
│  │  ┌───────────────────────────────────────────────────┐ ││
│  │  │ 🟢 call_12345  Personal Loan  ✅ Qualified  2m ago│ ││
│  │  │    Priya → Rahul Kumar  •  Duration: 4:23         │ ││
│  │  │    Nudges used: 3/5  •  [View Details]            │ ││
│  │  └───────────────────────────────────────────────────┘ ││
│  │  ┌───────────────────────────────────────────────────┐ ││
│  │  │ 🔴 call_12344  Home Loan  ⏸️ In Progress  5m ago  │ ││
│  │  │    Priya → Anita Singh  •  Duration: 6:47 (live) │ ││
│  │  │    [Monitor Call →]                               │ ││
│  │  └───────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Visual Features

- **Stats cards:** Glassmorphism with icon, number (large), metric label, trend indicator (↑/↓ with %)
- **Charts:** Modern gradients, animated on load
- **Call list:** Hover effect reveals quick actions, status color-coded
- **Filter bar:** Floating glass bar with dropdowns

---

## 4. Landing Page Redesign

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  SAARTHI                    [Features][Pricing][Login][Try]│
├─────────────────────────────────────────────────────────────┤
│                    ╔═══════════════════════╗                │
│                    ║   HERO SECTION        ║                │
│                    ║                       ║                │
│                ┌───║   AI Voice Agent      ║───┐            │
│                │   ║   for BFSI Products   ║   │            │
│            Animated║                       ║Animated        │
│             Orbs   ║  Qualify leads 3x     ║  Mesh          │
│                │   ║  faster with AI       ║   │            │
│                └───║                       ║───┘            │
│                    ║  [Start Free Trial →] ║                │
│                    ║  [Watch Demo 🎥]      ║                │
│                    ╚═══════════════════════╝                │
│                                                               │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                │
│  │ 🎯 Auto  │   │ 🧠 Smart │   │ 📊 Real  │                │
│  │ Qualify  │   │ Nudges   │   │ Analytics│                │
│  │ Leads    │   │ Agents   │   │ Insights │                │
│  └──────────┘   └──────────┘   └──────────┘                │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  PRODUCT SHOWCASE                                       ││
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       ││
│  │  │ 🏠     │  │ 💰     │  │ 🎓     │  │ 💳     │       ││
│  │  │ Home   │  │Personal│  │Education│ │ Credit │       ││
│  │  │ Loan   │  │ Loan   │  │ Loan   │  │ Card   │       ││
│  │  │ [Try→] │  │ [Try→] │  │ [Try→] │  │ [Try→] │       ││
│  │  └────────┘  └────────┘  └────────┘  └────────┘       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Visual Features

- **Hero:** Large gradient text, animated background mesh, CTA buttons with glow
- **Feature cards:** Glass cards with icons, hover lift effect
- **Product grid:** Cards with product icon, name, hover reveals "Try Now" button
- **Animations:** Parallax scroll, fade-in on viewport enter

---

## Color Palette

**Primary Gradient:** `from-blue-600 to-violet-600`
**Success:** `emerald-500`
**Warning:** `amber-500`
**Error:** `red-500`

**Backgrounds:**
- Base: `slate-950`
- Cards: `white/5 backdrop-blur`
- Borders: `white/10`

**Text:**
- Primary: `white`
- Secondary: `slate-400`
- Muted: `slate-500`

---

## Approve to code?

Review mockups. Changes needed? Or proceed with implementation?
