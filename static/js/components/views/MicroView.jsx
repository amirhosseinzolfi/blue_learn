const {
    Zap, Settings, Loader2, CheckCircle, Layout,
    Trophy, Sparkles, RefreshCw, ChevronLeft, Clock
} = window.Icons;

function MicroView({ dailyMicroCourses, courses, microSettings, setMicroSettings, onLoadMore, onCardClick, isDailyLoading, onApplySettings, isMicroSettingsOpen, setIsMicroSettingsOpen, dailyReadingMinutes }) {

    const completedCount = dailyMicroCourses.filter(i => i.is_completed).length;
    const progressPct = dailyMicroCourses.length > 0 ? (completedCount / dailyMicroCourses.length) * 100 : 0;
    const allDone = dailyMicroCourses.length > 0 && dailyMicroCourses.every(i => i.is_completed);

    // Format minutes nicely
    const formatMinutes = (mins) => {
        if (!mins || mins === 0) return '۰ دقیقه';
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        const toFa = n => n.toString().replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
        if (h > 0 && m > 0) return `${toFa(h)} ساعت و ${toFa(m)} دقیقه`;
        if (h > 0) return `${toFa(h)} ساعت`;
        return `${toFa(m)} دقیقه`;
    };

    return (
        <div className="bg-dark-lighter border border-purple-900/20 rounded-[2rem] p-6 md:p-10 shadow-[0_0_40px_rgba(0,0,0,0.5)]">

            {/* ── Daily Reading Time Badge ── */}
            <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold flex items-center gap-3 text-white">
                    <Zap className="text-primary" size={28} /> میکرو دوره‌های روزانه
                </h2>
                <div className="flex items-center gap-3">
                    {/* Daily time pill */}
                    <div className="group flex items-center gap-2 bg-gradient-to-r from-primary/15 to-indigo-500/10 border border-primary/25 px-4 py-2 rounded-full backdrop-blur-sm transition-all hover:from-primary/25 hover:border-primary/40" title="زمان مطالعه امروز">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                        <Clock size={13} className="text-primary/80" />
                        <span className="text-xs font-bold text-primary/90 tracking-wide">{formatMinutes(dailyReadingMinutes)}</span>
                        <span className="text-[10px] text-slate-500 font-medium hidden sm:inline">امروز</span>
                    </div>
                    {/* Settings button */}
                    <div className="relative">
                        <button onClick={() => setIsMicroSettingsOpen(o => !o)} className="p-2 text-slate-500 hover:text-white transition-all hover:rotate-90 duration-300" title="تنظیمات">
                            <Settings size={24} />
                        </button>
                        {isMicroSettingsOpen && (
                            <div className="absolute left-0 top-full mt-3 w-72 bg-dark-lightest border border-purple-900/30 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.7)] p-5 z-20 backdrop-blur-xl">
                                <h4 className="text-sm font-bold text-white mb-4 border-b border-purple-900/20 pb-3 flex items-center gap-2">
                                    <Settings size={16} className="text-primary" /> تنظیمات میکرو دوره
                                </h4>
                                <div className="mb-5">
                                    <label className="text-xs text-slate-400 block mb-2 font-medium">تعداد درس در هر دوره (روزانه)</label>
                                    <input type="number" min="1" max="10" value={microSettings.countPerCourse}
                                        onChange={(e) => setMicroSettings(s => ({ ...s, countPerCourse: parseInt(e.target.value) || 1 }))}
                                        className="w-full bg-dark-lighter border border-purple-900/50 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-primary transition-all"
                                    />
                                </div>
                                <div className="mb-5">
                                    <label className="text-xs text-slate-400 block mb-2 font-medium">دوره‌های فعال</label>
                                    <div className="max-h-40 overflow-y-auto space-y-2.5 pr-1">
                                        {courses.map(c => (
                                            <label key={c.id} className="flex items-center gap-3 text-sm text-slate-300 hover:text-white cursor-pointer">
                                                <input type="checkbox"
                                                    checked={microSettings.courseIds.length === 0 || microSettings.courseIds.includes(c.id)}
                                                    onChange={(e) => {
                                                        let ids = microSettings.courseIds.length === 0 ? courses.map(x => x.id) : [...microSettings.courseIds];
                                                        ids = e.target.checked ? [...new Set([...ids, c.id])] : ids.filter(id => id !== c.id);
                                                        if (ids.length === courses.length) ids = [];
                                                        setMicroSettings(s => ({ ...s, courseIds: ids }));
                                                    }}
                                                    className="w-4 h-4 accent-primary rounded cursor-pointer"
                                                />
                                                <span className="truncate hover:text-primary transition-colors">{c.short_title || c.title}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                <button onClick={onApplySettings} disabled={isDailyLoading}
                                    className="w-full bg-gradient-to-r from-primary to-indigo-600 text-white rounded-xl py-2.5 text-sm font-bold transition-all shadow-[0_0_15px_rgba(168,85,247,0.3)] disabled:opacity-70 flex items-center justify-center gap-2">
                                    {isDailyLoading ? <Loader2 size={16} className="animate-spin" /> : 'اعمال و بروزرسانی'}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Progress bar */}
            {dailyMicroCourses.length > 0 && (
                <div className="mb-10">
                    <div className="flex justify-between items-center text-xs mb-3 px-1">
                        <span className="text-slate-300 font-bold tracking-wide">پیشرفت روزانه شما</span>
                        <div className="bg-primary/20 px-3 py-1 rounded-full border border-primary/30">
                            <span className="text-primary font-bold">{Math.round(progressPct)}%</span>
                        </div>
                    </div>
                    <div className="w-full bg-dark-lightest/70 h-3.5 rounded-full overflow-hidden shadow-inner border border-purple-900/20">
                        <div className="bg-gradient-to-r from-primary via-indigo-500 to-purple-500 h-full transition-all duration-1000 ease-out relative" style={{ width: `${progressPct}%` }}>
                            <div className="absolute top-0 right-0 bottom-0 w-20 bg-gradient-to-r from-transparent to-white/30 animate-[shimmer_2s_infinite]" />
                        </div>
                    </div>
                    {allDone && (
                        <div className="mt-6 p-5 bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-2xl flex items-center justify-center gap-4 text-green-400 shadow-[0_0_30px_rgba(34,197,94,0.15)] relative overflow-hidden">
                            <div className="absolute inset-0 bg-white/5 animate-pulse" />
                            <Trophy size={28} className="drop-shadow-[0_0_10px_rgba(34,197,94,0.5)] z-10" />
                            <span className="font-bold text-lg z-10">تبریک! تمام میکرو دوره‌های امروز را به پایان رساندید!</span>
                            <Sparkles size={24} className="absolute right-6 top-1/2 -translate-y-1/2 opacity-50 z-10" />
                        </div>
                    )}
                </div>
            )}

            {/* Cards grid */}
            {dailyMicroCourses.length === 0 ? (
                <div className="text-center py-20 text-slate-400 bg-dark-lightest/20 rounded-3xl border border-dashed border-purple-900/30">
                    در حال حاضر هیچ درس ناتمامی برای پیشنهاد روزانه وجود ندارد.
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {dailyMicroCourses.map(item => {
                        const mColor = getCourseColor(item.course_color);
                        return (
                            <div key={item.item_id} onClick={() => onCardClick(item)}
                                className={`relative backdrop-blur-sm border p-8 rounded-[2rem] hover:-translate-y-1.5 transition-all duration-400 cursor-pointer group flex flex-col overflow-hidden min-h-[180px] shadow-lg ${item.is_completed ? 'bg-green-500/5 border-green-500/30 hover:border-green-400/50 hover:shadow-[0_15px_40px_-10px_rgba(34,197,94,0.2)]' : `bg-dark-lightest/30 border-purple-900/20 hover:bg-dark-lightest/50 ${mColor.classes.hoverBorder} ${mColor.classes.shadowHover}`}`}>
                                {!item.is_completed && <div className={`absolute top-0 left-0 w-32 h-32 ${mColor.classes.bgLight} rounded-full blur-3xl -ml-16 -mt-16 group-hover:opacity-40 transition-all duration-500 opacity-20`} />}
                                {item.is_completed && <div className="absolute top-0 left-0 w-32 h-32 bg-green-500/10 rounded-full blur-3xl -ml-16 -mt-16 group-hover:bg-green-500/20 transition-all duration-500" />}
                                <div className="relative z-10 flex-1 flex flex-col">
                                    <div className="flex items-center gap-3 mb-5">
                                        <div className={`p-2.5 rounded-xl transition-colors ${item.is_completed ? 'bg-green-500/20 group-hover:bg-green-500/30' : `${mColor.classes.bgLight}`}`}>
                                            {item.is_completed ? <CheckCircle size={18} className="text-green-500" /> : <Zap size={18} className={mColor.classes.text} />}
                                        </div>
                                        <span className={`text-xs font-bold uppercase tracking-wider ${item.is_completed ? 'text-green-400/80' : mColor.classes.text}`}>{item.course_title}</span>
                                    </div>
                                    <h3 className={`text-xl font-bold mb-3 transition-colors ${item.is_completed ? 'text-slate-300 group-hover:text-green-300' : 'text-slate-200 group-hover:text-white'} ${isEnglish(item.item_title) ? 'ltr-content' : ''}`}>{item.item_title}</h3>
                                    <div className="mt-auto pt-4 flex items-center justify-between">
                                        <p className={`text-xs font-medium flex items-center gap-1.5 ${item.is_completed ? 'text-green-500/60' : 'text-slate-500'}`}>
                                            <Layout size={14} className="opacity-70" /> {item.chapter || 'فصل نامشخص'}
                                        </p>
                                        <div className={`opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 ${item.is_completed ? 'text-green-400' : mColor.classes.text}`}>
                                            <ChevronLeft size={20} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Load more */}
            {dailyMicroCourses.length > 0 && !allDone && (
                <div className="mt-10 flex justify-center border-t border-purple-900/20 pt-6">
                    <button onClick={onLoadMore} disabled={isDailyLoading} className="text-slate-400 hover:text-primary transition-colors text-sm font-medium flex items-center gap-2 group disabled:opacity-50">
                        <span className="bg-dark-lightest/50 p-2 rounded-full group-hover:bg-primary/10 transition-colors">
                            <RefreshCw size={16} className={`transition-transform duration-500 ${isDailyLoading ? 'animate-spin' : 'group-hover:rotate-180'}`} />
                        </span>
                        {isDailyLoading ? 'در حال بارگذاری...' : 'بارگذاری میکرو دوره‌های بیشتر'}
                    </button>
                </div>
            )}
        </div>
    );
}
