const API_BASE = window.location.origin;

const COURSE_COLORS = [
    { name: 'purple', label: 'بنفش', hex: '#a855f7', classes: { border: 'border-purple-900/20', hoverBorder: 'hover:border-purple-500/40', text: 'text-primary', hoverText: 'group-hover:text-primary', from: 'from-primary', to: 'to-indigo-500', bgLight: 'bg-primary/20', shadowHover: 'hover:shadow-[0_0_30px_rgba(168,85,247,0.15)]', dropShadow: 'drop-shadow-[0_0_8px_rgba(168,85,247,0.5)]', glow: 'bg-primary/10' } },
    { name: 'blue',   label: 'آبی',      hex: '#3b82f6', classes: { border: 'border-blue-900/20',   hoverBorder: 'hover:border-blue-500/40',    text: 'text-blue-500',    hoverText: 'group-hover:text-blue-500',    from: 'from-blue-500',    to: 'to-cyan-500',    bgLight: 'bg-blue-500/20',    shadowHover: 'hover:shadow-[0_0_30px_rgba(59,130,246,0.15)]',    dropShadow: 'drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]',    glow: 'bg-blue-500/10' } },
    { name: 'emerald',label: 'زمردی',    hex: '#10b981', classes: { border: 'border-emerald-900/20', hoverBorder: 'hover:border-emerald-500/40', text: 'text-emerald-500', hoverText: 'group-hover:text-emerald-500', from: 'from-emerald-500', to: 'to-teal-500',  bgLight: 'bg-emerald-500/20', shadowHover: 'hover:shadow-[0_0_30px_rgba(16,185,129,0.15)]',  dropShadow: 'drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]',   glow: 'bg-emerald-500/10' } },
    { name: 'rose',   label: 'قرمز',     hex: '#f43f5e', classes: { border: 'border-rose-900/20',   hoverBorder: 'hover:border-rose-500/40',   text: 'text-rose-500',   hoverText: 'group-hover:text-rose-500',   from: 'from-rose-500',   to: 'to-orange-500', bgLight: 'bg-rose-500/20',   shadowHover: 'hover:shadow-[0_0_30px_rgba(244,63,94,0.15)]',   dropShadow: 'drop-shadow-[0_0_8px_rgba(244,63,94,0.5)]',    glow: 'bg-rose-500/10' } },
    { name: 'amber',  label: 'کهربایی', hex: '#f59e0b', classes: { border: 'border-amber-900/20',  hoverBorder: 'hover:border-amber-500/40',  text: 'text-amber-500',  hoverText: 'group-hover:text-amber-500',  from: 'from-amber-500',  to: 'to-yellow-500', bgLight: 'bg-amber-500/20',  shadowHover: 'hover:shadow-[0_0_30px_rgba(245,158,11,0.15)]',  dropShadow: 'drop-shadow-[0_0_8px_rgba(245,158,11,0.5)]',   glow: 'bg-amber-500/10' } },
    { name: 'cyan',   label: 'فیروزه‌ای',hex: '#06b6d4', classes: { border: 'border-cyan-900/20',   hoverBorder: 'hover:border-cyan-500/40',   text: 'text-cyan-500',   hoverText: 'group-hover:text-cyan-500',   from: 'from-cyan-500',   to: 'to-blue-500',   bgLight: 'bg-cyan-500/20',   shadowHover: 'hover:shadow-[0_0_30px_rgba(6,182,212,0.15)]',   dropShadow: 'drop-shadow-[0_0_8px_rgba(6,182,212,0.5)]',    glow: 'bg-cyan-500/10' } },
];

const getCourseColor = (name) => COURSE_COLORS.find(c => c.name === name) || COURSE_COLORS[0];

const isEnglish = (text) => {
    if (!text) return false;
    const eng = (text.match(/[a-zA-Z]/g) || []).length;
    const fa  = (text.match(/[\u0600-\u06FF]/g) || []).length;
    return eng > fa;
};

const formatTime = (seconds) => {
    const t = parseInt(seconds) || 0;
    const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = t % 60;
    if (h > 0) return `${h} ساعت و ${m} دقیقه`;
    if (m > 0) return `${m} دقیقه و ${s} ثانیه`;
    return `${s} ثانیه`;
};
