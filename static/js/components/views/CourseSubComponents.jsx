const {
    Layout, Trophy, MoreVertical, Settings, Trash2,
    BarChart, BookOpen, ChevronRight, Clock, Play,
    CheckCircle, ChevronLeft, Zap, Bot, Loader2,
    RefreshCw, Copy, Sparkles, Maximize, Send, X,
    Star, Target, Flame
} = window.Icons;

// ── Chapter accordion in the sidebar ──────────────────────────────────────
function ChapterNav({ course, viewingItem, vColor, openChapters, setOpenChapters, onItemClick }) {
    const chapters = Object.entries(
        course.items.reduce((acc, item) => {
            const ch = item.chapter || 'سایر';
            if (!acc[ch]) acc[ch] = [];
            acc[ch].push(item); return acc;
        }, {})
    );
    return chapters.map(([chapter, items], cIdx) => {
        const isDone = items.every(i => i.is_completed);
        const isOpen = openChapters[chapter];
        return (
            <div key={chapter} className="shrink-0 rounded-2xl overflow-hidden flex flex-col border border-purple-900/15 bg-dark-lightest/30">
                <div onClick={() => setOpenChapters(p => ({ ...p, [chapter]: !p[chapter] }))}
                    className="p-3.5 px-4 cursor-pointer flex items-center justify-between transition-colors">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                        <span className={`flex items-center justify-center w-6 h-6 text-sm font-bold shrink-0 ${isDone ? 'text-green-400' : vColor.classes.text}`}>
                            {isDone ? <CheckCircle size={16} /> : cIdx + 1}
                        </span>
                        <span className="font-semibold text-[13px] truncate text-slate-200">{chapter}</span>
                    </div>
                    <ChevronLeft size={14} className={`text-slate-500 shrink-0 transition-transform duration-200 ${isOpen ? '-rotate-90' : ''}`} />
                </div>
                {isOpen && (
                    <div className="flex flex-col gap-0.5 px-3 pb-3">
                        {items.map((item, sIdx) => (
                            <div key={item.id} onClick={() => onItemClick(item)}
                                className={`py-2.5 px-2.5 rounded-xl text-xs font-medium cursor-pointer transition-all flex items-center gap-2.5 ${item.id === viewingItem?.id ? vColor.classes.text : 'text-slate-400 hover:text-slate-300 hover:bg-white/[0.04]'}`}>
                                {item.is_completed
                                    ? <CheckCircle size={12} className="text-green-500 shrink-0" />
                                    : <span className={`w-4 text-center text-[10px] font-bold shrink-0 ${item.id === viewingItem?.id ? vColor.classes.text : 'text-slate-500'}`}>{sIdx + 1}</span>
                                }
                                <span className="flex-1 leading-relaxed">{item.title}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    });
}

// ── Roadmap (course outline view) ─────────────────────────────────────────
function CourseRoadmap({ course, sColor, onItemClick, viewingItem }) {
    const totalItems = course.items.length;
    const completedCount = course.items.filter(i => i.is_completed).length;

    // Find the next recommended lesson (first non-completed)
    const nextRecommended = course.items.find(i => !i.is_completed);

    return (
        <div className={`bg-dark-lighter border ${sColor.classes.border} rounded-[2.5rem] p-6 md:p-12 shadow-[0_0_60px_rgba(0,0,0,0.6)] relative overflow-hidden`}>
            
            {/* Background decorative blurs using semantic color */}
            <div className={`absolute top-0 right-0 w-80 h-80 ${sColor.classes.glow} rounded-full blur-[120px] pointer-events-none opacity-20`} />
            <div className={`absolute bottom-0 left-0 w-96 h-96 ${sColor.classes.bgLight} rounded-full blur-[150px] pointer-events-none opacity-10`} />

            {/* Simplified Header */}
            <div className="flex items-center gap-5 mb-14 relative z-10">
                <div className={`p-4 rounded-3xl ${sColor.classes.bgLight} shadow-xl border border-white/10 backdrop-blur-md`}>
                    <BookOpen className={sColor.classes.text} size={28} />
                </div>
                <div>
                    <h3 className="text-2xl md:text-3xl font-black text-white tracking-tight">مسیر یادگیری هوشمند</h3>
                    <div className="flex items-center gap-3 mt-2">
                        <span className="text-sm text-slate-400 font-medium">سرفصل‌های این دوره آموزشی</span>
                        <div className="w-1 h-1 rounded-full bg-slate-600" />
                        <span className={`text-xs font-bold ${sColor.classes.text}`}>{totalItems} درس تخصصی</span>
                    </div>
                </div>
            </div>

            {/* Session Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 relative z-10">
                {course.items.map((item, idx) => {
                    const isActive = item.id === viewingItem?.id;
                    const isCompleted = item.is_completed;
                    const isNext = nextRecommended && item.id === nextRecommended.id;
                    
                    return (
                        <div key={item.id} onClick={() => onItemClick(item)}
                            className={`group relative p-8 rounded-[2.5rem] border transition-all duration-500 cursor-pointer overflow-hidden flex flex-col min-h-[220px]
                                ${isCompleted 
                                    ? 'bg-green-500/[0.02] border-green-500/10 hover:border-green-500/30' 
                                    : isNext
                                        ? `bg-dark-lightest/40 ${sColor.classes.border} shadow-[0_20px_50px_rgba(0,0,0,0.4)] scale-[1.03] ring-1 ring-primary/30`
                                        : `bg-dark-lightest/15 border-white/5 hover:bg-dark-lightest/30 ${sColor.classes.hoverBorder} hover:shadow-2xl`
                                }`}>
                            
                            {/* Visual Accents & Gamification Glows */}
                            {isNext && <div className={`absolute -top-10 -right-10 w-32 h-32 ${sColor.classes.glow} rounded-full blur-[60px] opacity-40 animate-pulse`} />}
                            
                            <div className="relative z-10 flex flex-col h-full">
                                {/* Top Badges Section */}
                                <div className="flex justify-between items-center mb-6">
                                    <div className="flex flex-col gap-1">
                                        <span className={`text-[9px] font-black uppercase tracking-[0.2em] opacity-60
                                            ${isCompleted ? 'text-green-500' : sColor.classes.text}`}>
                                            {item.chapter || 'بخش اصلی'}
                                        </span>
                                        <div className={`h-0.5 w-6 rounded-full transition-all duration-500 group-hover:w-12
                                            ${isCompleted ? 'bg-green-500/40' : `bg-gradient-to-r ${sColor.classes.from} to-transparent opacity-50`}`} />
                                    </div>
                                    
                                    <div className="flex items-center gap-2">
                                        {isNext && (
                                            <div className="bg-primary/20 text-primary px-3 py-1 rounded-full text-[9px] font-bold border border-primary/20 flex items-center gap-1.5 animate-bounce-subtle">
                                                <Target size={10} /> پیشنهاد بعدی
                                            </div>
                                        )}
                                        {isCompleted && (
                                            <div className="bg-green-500/10 text-green-500 p-1.5 rounded-full border border-green-500/20">
                                                <CheckCircle size={14} />
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Main Session Title */}
                                <h4 className={`text-lg font-bold leading-[1.6] mb-8 flex-1 transition-all duration-300
                                    ${isCompleted ? 'text-slate-500 group-hover:text-slate-300' : 'text-slate-100 group-hover:text-white'}
                                    ${isEnglish(item.title) ? 'ltr-content' : ''}`}>
                                    {item.title}
                                </h4>

                                {/* Gamified Footer Section */}
                                <div className="mt-auto pt-6 border-t border-white/5 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        {/* Minimal Gamification: XP/Level concept */}
                                        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-dark/40 border border-white/5`}>
                                            <Star size={10} className={isCompleted ? 'text-yellow-500' : 'text-slate-500'} fill={isCompleted ? 'currentColor' : 'none'} />
                                            <span className="text-[10px] font-mono font-bold text-slate-400">10 XP</span>
                                        </div>
                                        {item.study_time > 0 && (
                                            <div className="flex items-center gap-1.5 opacity-50">
                                                <Clock size={11} className="text-slate-500" />
                                                <span className="text-[10px] font-mono text-slate-500">{Math.round(item.study_time / 60)}m</span>
                                            </div>
                                        )}
                                    </div>
                                    
                                    <div className="flex items-center gap-3">
                                        {!isCompleted ? (
                                            <div className={`flex items-center gap-1.5 px-4 py-1.5 rounded-2xl transition-all duration-300
                                                ${isNext 
                                                    ? `bg-gradient-to-r ${sColor.classes.from} ${sColor.classes.to} text-white shadow-lg` 
                                                    : 'bg-white/5 text-slate-400 group-hover:bg-primary/10 group-hover:text-primary'}`}>
                                                <span className="text-[10px] font-bold uppercase tracking-tight">
                                                    {item.content ? 'شروع یادگیری' : 'تولید درس'}
                                                </span>
                                                <Play size={10} fill="currentColor" className="rotate-180" />
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-1.5 px-3 py-1 bg-green-500/5 rounded-full opacity-60">
                                                <Flame size={12} className="text-green-500" />
                                                <span className="text-[9px] font-bold text-green-500 uppercase">کامل شد</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
