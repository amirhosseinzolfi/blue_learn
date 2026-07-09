const { useState, useEffect, useRef } = React;
const {
    Globe, Search, Users, BarChart, BookOpen, Clock, Sparkles, ChevronRight,
    ChevronLeft, CheckCircle, Loader2, X, Zap, Star, Target, Play
} = window.Icons;

// ── Star Rating (interactive + read-only) ───────────────────────────────────
function StarRating({ value = 0, count = null, onChange = null, size = 16, readOnly = false }) {
    const [hover, setHover] = useState(0);
    const active = hover || value;
    return (
        <div className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map(n => (
                <button
                    key={n}
                    type="button"
                    disabled={readOnly}
                    onMouseEnter={() => !readOnly && setHover(n)}
                    onMouseLeave={() => !readOnly && setHover(0)}
                    onClick={(e) => { e.stopPropagation(); if (onChange) onChange(n); }}
                    className={`transition-transform ${readOnly ? 'cursor-default' : 'hover:scale-125 cursor-pointer'} ${n <= active ? 'text-amber-400' : 'text-slate-700'}`}
                >
                    <Star size={size} fill={n <= active ? 'currentColor' : 'none'} />
                </button>
            ))}
            {count !== null && (
                <span className="text-[11px] text-slate-500 font-medium mr-1">
                    {value > 0 ? value.toFixed(1) : '—'}
                    {count > 0 && <span className="opacity-70"> ({count})</span>}
                </span>
            )}
        </div>
    );
}

// ── Global Course Card (catalog entry) ──────────────────────────────────────
function GlobalCourseCard({ course, onOpen, onEnroll, enrollingId }) {
    const c = getCourseColor(course.color);
    const isEnrolling = enrollingId === course.id;
    const displayHours = course.total_estimated_hours || course.hours;
    const description = course.course_description || course.description;

    return (
        <div
            onClick={() => onOpen(course)}
            className={`bg-dark-lighter border ${c.classes.border} p-0 rounded-[2rem] overflow-hidden ${c.classes.hoverBorder} transition-all duration-300 group relative shadow-lg shadow-black/20 ${c.classes.shadowHover} flex flex-col cursor-pointer`}
        >
            {/* Cover */}
            {course.cover_image ? (
                <div className="w-full h-36 md:h-44 relative overflow-hidden shrink-0">
                    <img src={course.cover_image} alt={course.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out" />
                    <div className="absolute inset-0 bg-gradient-to-t from-dark-lighter via-dark-lighter/30 to-transparent" />
                </div>
            ) : (
                <div className={`w-full h-36 md:h-44 relative overflow-hidden shrink-0 ${c.classes.bgLight}`}>
                    <div className={`absolute -top-10 -right-10 w-40 h-40 ${c.classes.glow} rounded-full blur-[60px]`} />
                    <div className="absolute inset-0 flex items-center justify-center">
                        <BookOpen size={40} className={`${c.classes.text} opacity-50`} />
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-t from-dark-lighter via-transparent to-transparent" />
                </div>
            )}

            {/* Enrolled badge */}
            {course.is_enrolled && (
                <div className="absolute top-4 left-4 z-10 flex items-center gap-1.5 bg-green-500/20 border border-green-500/30 backdrop-blur-md px-2.5 py-1 rounded-full text-[10px] font-bold text-green-400">
                    <CheckCircle size={11} /> ثبت‌نام شده
                </div>
            )}

            {/* Body */}
            <div className="flex flex-col flex-1 p-6 gap-3.5">
                <div className="flex flex-col gap-2">
                    <h3 className={`text-xl font-bold ${c.classes.hoverText} transition-colors text-slate-100 flex-1 leading-snug ${isEnglish(course.short_title || course.title) ? 'ltr-content' : ''}`}>
                        {course.short_title || course.title}
                    </h3>
                    {description && (
                        <p className={`text-xs text-slate-400 leading-relaxed line-clamp-2 ${isEnglish(description) ? 'ltr-content' : ''}`}>
                            {description}
                        </p>
                    )}
                </div>

                {/* Rating row */}
                <div className="flex items-center justify-between">
                    <StarRating value={course.avg_rating || 0} count={course.rating_count || 0} readOnly size={14} />
                    <span className="flex items-center gap-1 text-[11px] text-slate-500 font-medium">
                        <Users size={12} /> {course.enrollment_count || 0}
                    </span>
                </div>

                {/* Meta chips */}
                <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-500 font-medium">
                    {course.level && (
                        <span className={`flex items-center gap-1.5 ${c.classes.bgLight} px-2.5 py-1 rounded-lg border ${c.classes.border}`}>
                            <BarChart size={12} className={c.classes.text} /> {course.level}
                        </span>
                    )}
                    {course.sessions && (
                        <span className="flex items-center gap-1.5 bg-dark-lightest/60 px-2.5 py-1 rounded-lg border border-purple-900/20">
                            <BookOpen size={12} /> {course.sessions} درس
                        </span>
                    )}
                    {displayHours && (
                        <span className="flex items-center gap-1.5 bg-dark-lightest/60 px-2.5 py-1 rounded-lg border border-purple-900/20">
                            <Clock size={12} /> {displayHours}h
                        </span>
                    )}
                </div>

                {/* Author */}
                <div className="flex items-center gap-2 pt-3 mt-auto border-t border-purple-900/15">
                    <div className={`w-7 h-7 shrink-0 rounded-full ${c.classes.bgLight} border ${c.classes.border} flex items-center justify-center`}>
                        <Users size={13} className={c.classes.text} />
                    </div>
                    <span className="text-xs text-slate-400 font-medium truncate">{course.author_name || 'کاربر بلو'}</span>
                </div>

                {/* Action */}
                {course.is_enrolled ? (
                    <button
                        onClick={(e) => { e.stopPropagation(); onOpen(course); }}
                        className="w-full bg-green-500/10 border border-green-500/25 text-green-400 py-3 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-green-500/15 active:scale-[0.98] transition-all"
                    >
                        <CheckCircle size={18} /> مشاهده دوره
                    </button>
                ) : (
                    <button
                        onClick={(e) => { e.stopPropagation(); onEnroll(course); }}
                        disabled={isEnrolling}
                        className={`w-full bg-gradient-to-r ${c.classes.from} ${c.classes.to} text-white py-3 rounded-2xl font-bold flex items-center justify-center gap-2 ${c.classes.shadowHover} hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-70 disabled:cursor-wait`}
                    >
                        {isEnrolling ? (
                            <><Loader2 size={18} className="animate-spin" /> در حال ثبت‌نام...</>
                        ) : (
                            <><Zap size={18} className="fill-current" /> ثبت‌نام سریع</>
                        )}
                    </button>
                )}
            </div>
        </div>
    );
}

// ── Global Outline Roadmap (read-only session cards) ────────────────────────
function GlobalOutline({ items, sColor }) {
    if (!items || items.length === 0) {
        return (
            <p className="text-sm text-slate-500 text-center py-8">سرفصلی برای این دوره ثبت نشده است.</p>
        );
    }
    // Group by chapter
    const chapters = Object.entries(
        items.reduce((acc, item) => {
            const ch = item.chapter || 'سایر';
            if (!acc[ch]) acc[ch] = [];
            acc[ch].push(item);
            return acc;
        }, {})
    );

    return (
        <div className="flex flex-col gap-10">
            {chapters.map(([chapter, chItems], cIdx) => (
                <div key={chapter} className="flex flex-col gap-4">
                    {/* Chapter header */}
                    <div className="flex items-center gap-3">
                        <div className={`flex items-center justify-center w-8 h-8 text-sm font-bold shrink-0 rounded-xl ${sColor.classes.bgLight} border ${sColor.classes.border} ${sColor.classes.text}`}>
                            {cIdx + 1}
                        </div>
                        <div className="flex flex-col">
                            <h4 className="text-base font-bold text-white leading-tight">{chapter}</h4>
                            <span className={`text-[11px] ${sColor.classes.text} font-medium`}>{chItems.length} درس</span>
                        </div>
                        <div className={`flex-1 h-px ml-2 bg-gradient-to-l ${sColor.classes.from} to-transparent opacity-20`} />
                    </div>
                    {/* Session cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {chItems.map((item, sIdx) => (
                            <div
                                key={item.id}
                                className={`group relative p-6 rounded-[1.75rem] border transition-all duration-500 overflow-hidden flex flex-col min-h-[160px] bg-dark-lightest/15 border-white/5 hover:bg-dark-lightest/30 ${sColor.classes.hoverBorder} hover:shadow-xl`}
                            >
                                <div className="relative z-10 flex flex-col h-full">
                                    <div className="flex flex-col gap-1 mb-3">
                                        <span className={`text-[9px] font-black uppercase tracking-[0.2em] opacity-60 ${sColor.classes.text}`}>
                                            {item.chapter || 'بخش اصلی'}
                                        </span>
                                        <div className={`h-0.5 w-6 rounded-full bg-gradient-to-r ${sColor.classes.from} to-transparent opacity-50`} />
                                    </div>
                                    <h4 className={`text-sm font-bold leading-[1.6] mb-2 flex-1 text-slate-100 group-hover:text-white transition-all duration-300 ${isEnglish(item.title) ? 'ltr-content' : ''}`}>
                                        {item.title}
                                    </h4>
                                    {item.description && (
                                        <p className={`text-xs text-slate-400 leading-relaxed line-clamp-2 ${isEnglish(item.description) ? 'ltr-content' : ''}`}>
                                            {item.description}
                                        </p>
                                    )}
                                    <div className="mt-auto pt-4 border-t border-white/5 flex items-center justify-between">
                                        <span className="text-[10px] font-mono font-bold text-slate-500">درس {sIdx + 1}</span>
                                        <div className={`flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white/5 text-slate-400 group-hover:bg-primary/10 group-hover:text-primary transition-all`}>
                                            <span className="text-[9px] font-bold uppercase">پیش‌نمایش</span>
                                            <BookOpen size={10} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

// ── Global Courses Catalog View ─────────────────────────────────────────────
function GlobalCoursesView({ onBack, onEnrolled, onOpenCourse, showToast }) {
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [sort, setSort] = useState('recent');
    const [enrollingId, setEnrollingId] = useState(null);
    const [detailCourse, setDetailCourse] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const debounceRef = useRef(null);

    useEffect(() => {
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => setDebouncedSearch(search), 350);
        return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
    }, [search]);

    const loadCourses = (term = '', sortKey = 'recent') => {
        setLoading(true);
        api.fetchGlobalCourses(term, sortKey)
            .then(setCourses)
            .catch(err => { console.error(err); showToast('خطا در دریافت دوره‌های عمومی', 'error'); })
            .finally(() => setLoading(false));
    };

    useEffect(() => { loadCourses(debouncedSearch, sort); }, [debouncedSearch, sort]);

    // Patch a single course in the local list (e.g. after enroll/rate) without refetch
    const patchCourse = (id, patch) => {
        setCourses(prev => prev.map(c => c.id === id ? { ...c, ...patch } : c));
    };

    const handleEnroll = async (course) => {
        setEnrollingId(course.id);
        try {
            const updated = await api.enrollGlobalCourse(course.id);
            patchCourse(course.id, { is_enrolled: true, enrollment_count: updated.enrollment_count });
            if (detailCourse?.id === course.id) setDetailCourse(prev => ({ ...prev, is_enrolled: true, enrollment_count: updated.enrollment_count }));
            showToast(`دوره «${course.short_title || course.title}» به دوره‌های شما اضافه شد!`);
            if (onEnrolled) onEnrolled();
        } catch (err) {
            const detail = err?.response?.data?.detail;
            showToast(detail || 'خطا در ثبت‌نام', 'error');
        } finally {
            setEnrollingId(null);
        }
    };

    // Open detail: fetch full course WITH outline items
    const handleOpen = async (course) => {
        setDetailCourse(course);
        setDetailLoading(true);
        try {
            const full = await api.fetchGlobalCourse(course.id);
            setDetailCourse(full);
        } catch (err) {
            console.error(err);
        } finally {
            setDetailLoading(false);
        }
    };

    const handleRate = async (courseId, rating) => {
        try {
            const updated = await api.rateGlobalCourse(courseId, rating);
            patchCourse(courseId, updated);
            if (detailCourse?.id === courseId) setDetailCourse(prev => ({ ...prev, ...updated, items: prev.items }));
            showToast('از امتیاز شما سپاسگزاریم!');
        } catch (err) {
            showToast('خطا در ثبت امتیاز', 'error');
        }
    };

    // ── Detail page ──
    if (detailCourse) {
        return (
            <GlobalCourseDetail
                course={detailCourse}
                loading={detailLoading}
                onBack={() => setDetailCourse(null)}
                onEnroll={handleEnroll}
                onRate={handleRate}
                onOpenCourse={onOpenCourse}
                enrollingId={enrollingId}
                showToast={showToast}
            />
        );
    }

    return (
        <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-6 duration-500">
            {/* ── Header ── */}
            <div className="relative bg-dark-lighter/40 backdrop-blur-2xl border border-white/[0.05] rounded-[2.5rem] p-6 md:p-8 overflow-hidden shadow-[0_20px_50px_-20px_rgba(0,0,0,0.6)]">
                <div className="absolute top-[-30%] right-[-5%] w-80 h-80 bg-primary/15 blur-[120px] rounded-full pointer-events-none" />
                <div className="absolute bottom-[-40%] left-[-5%] w-72 h-72 bg-indigo-500/10 blur-[100px] rounded-full pointer-events-none" />

                <div className="relative z-10 flex flex-col gap-5">
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-gradient-to-tr from-primary to-indigo-500 rounded-2xl flex items-center justify-center text-white shadow-[0_0_30px_rgba(168,85,247,0.4)]">
                                <Globe size={24} />
                            </div>
                            <div>
                                <h2 className="text-2xl md:text-3xl font-black text-white tracking-tight">دوره‌های عمومی</h2>
                                <p className="text-xs text-slate-400 mt-1">دوره‌های ساخته‌شده توسط کاربران بلو لرن — کاوش و ثبت‌نام کنید</p>
                            </div>
                        </div>
                        <button onClick={onBack} className="flex items-center gap-2 text-slate-400 hover:text-white text-sm font-bold bg-dark-lightest/50 px-4 py-2.5 rounded-xl border border-purple-900/20 hover:bg-dark-lightest transition-all group/back">
                            <ChevronRight size={18} className="group-hover/back:translate-x-1 transition-transform" /> دوره‌های من
                        </button>
                    </div>

                    {/* ── Unified search + sort toolbar (one row) ── */}
                    <div className="flex flex-col md:flex-row md:items-center gap-3">
                        {/* Search */}
                        <div className="relative flex-1 min-w-0">
                            <Search size={18} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
                            <input
                                type="text"
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                placeholder="جستجوی دوره..."
                                className="w-full bg-dark-lightest/60 border border-purple-900/20 rounded-2xl py-3 pr-12 pl-11 text-sm text-white focus:outline-none focus:border-primary/50 transition-all placeholder:text-slate-500"
                            />
                            {search && (
                                <button onClick={() => setSearch('')} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors">
                                    <X size={16} />
                                </button>
                            )}
                        </div>

                        {/* Sort pills */}
                        <div className="flex items-center gap-1.5 bg-dark-lightest/40 border border-purple-900/20 p-1 rounded-2xl shrink-0 overflow-x-auto">
                            {[
                                { key: 'recent',        label: 'جدیدترین',      icon: Clock },
                                { key: 'top_rated',     label: 'بیشترین امتیاز', icon: Star },
                                { key: 'most_enrolled', label: 'محبوب‌ترین',     icon: Users },
                            ].map(({ key, label, icon: Icon }) => (
                                <button
                                    key={key}
                                    onClick={() => setSort(key)}
                                    className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                                        sort === key
                                            ? 'bg-primary/20 text-primary border border-primary/30 shadow-[0_0_15px_rgba(168,85,247,0.15)]'
                                            : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
                                    }`}
                                >
                                    <Icon size={13} /> {label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Result count ── */}
            {!loading && courses.length > 0 && (
                <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                    <Sparkles size={14} className="text-primary" />
                    <span>{courses.length} دوره</span>
                </div>
            )}

            {/* ── Body ── */}
            {loading ? (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                    <div className="relative w-16 h-16 mb-5">
                        <div className="absolute inset-0 border-4 border-purple-900/30 rounded-full" />
                        <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent animate-spin" />
                        <Globe className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-primary" size={20} />
                    </div>
                    <p className="text-slate-400 text-sm">در حال بارگذاری دوره‌های عمومی...</p>
                </div>
            ) : courses.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24 text-center animate-in fade-in duration-500">
                    <div className="w-16 h-16 bg-dark-lightest/60 rounded-2xl flex items-center justify-center text-slate-600 mb-5 border border-purple-900/20">
                        <Globe size={28} />
                    </div>
                    <h4 className="text-lg font-bold text-white mb-2">
                        {search ? 'دوره‌ای با این عبارت یافت نشد' : 'هنوز دوره عمومی‌ای منتشر نشده است'}
                    </h4>
                    <p className="text-slate-400 text-sm max-w-sm">
                        {search ? 'عبارت دیگری را امتحان کنید.' : 'اولین نفری باشید که دوره خود را برای همه کاربران منتشر می‌کند!'}
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {courses.map(course => (
                        <GlobalCourseCard key={course.id} course={course} onOpen={handleOpen} onEnroll={handleEnroll} enrollingId={enrollingId} />
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Global Course Detail Page ───────────────────────────────────────────────
function GlobalCourseDetail({ course, loading, onBack, onEnroll, onRate, onOpenCourse, enrollingId }) {
    const c = getCourseColor(course.color);
    const isEnrolling = enrollingId === course.id;
    const displayHours = course.total_estimated_hours || course.hours;
    const description = course.course_description || course.description;
    const learningOutcomes = course.learning_outcomes || [];
    const prerequisites = course.prerequisites || [];
    const items = course.items || [];

    return (
        <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-6 duration-500">
            {/* ── Hero card ── */}
            <div className={`relative bg-dark-lighter/60 backdrop-blur-xl border ${c.classes.border} rounded-[2.5rem] overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)]`}>
                <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
                    <div className={`absolute -top-20 -left-20 w-64 h-64 ${c.classes.glow} rounded-full blur-[80px]`} />
                    <div className={`absolute -bottom-32 -right-32 w-80 h-80 ${c.classes.bgLight} rounded-full blur-[100px]`} />
                </div>

                {course.cover_image && (
                    <div className="w-full h-48 md:h-64 relative border-b border-purple-900/20 shrink-0 z-0">
                        <img src={course.cover_image} alt="" className="w-full h-full object-cover" />
                        <div className="absolute inset-0 bg-gradient-to-t from-dark-lighter to-transparent" />
                    </div>
                )}

                <div className="relative z-10 flex flex-col gap-6 p-8 md:p-10">
                    <div className="flex justify-between items-center">
                        <button onClick={onBack} className="flex items-center gap-2 text-slate-400 hover:text-white text-sm font-bold bg-dark-lightest/50 px-4 py-2 rounded-xl border border-purple-900/20 hover:bg-dark-lightest transition-all group/back">
                            <ChevronRight size={18} className="group-hover/back:translate-x-1 transition-transform" /> بازگشت به دوره‌های عمومی
                        </button>
                        {course.is_enrolled && (
                            <div className="flex items-center gap-1.5 bg-green-500/20 border border-green-500/30 px-3 py-1.5 rounded-xl text-xs font-bold text-green-400">
                                <CheckCircle size={14} /> شما در این دوره ثبت‌نام کرده‌اید
                            </div>
                        )}
                    </div>

                    <div>
                        <h2 className={`text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight ${isEnglish(course.short_title || course.title) ? 'ltr-content' : ''}`}>
                            {course.short_title || course.title}
                        </h2>
                        {description && (
                            <p className={`text-slate-300 text-sm md:text-base leading-relaxed max-w-4xl opacity-90 ${isEnglish(description) ? 'ltr-content' : ''}`}>{description}</p>
                        )}
                    </div>

                    {/* Rating summary */}
                    <div className="flex items-center gap-6 flex-wrap">
                        <div className="flex flex-col gap-1">
                            <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">امتیاز دوره</span>
                            <div className="flex items-center gap-3">
                                <span className="text-2xl font-black text-white">{course.avg_rating ? course.avg_rating.toFixed(1) : '—'}</span>
                                <StarRating value={course.avg_rating || 0} readOnly size={18} />
                                <span className="text-xs text-slate-500">({course.rating_count || 0} رأی)</span>
                            </div>
                        </div>
                        <div className="h-10 w-px bg-white/10" />
                        <div className="flex flex-col gap-1">
                            <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">ثبت‌نام‌کنندگان</span>
                            <div className="flex items-center gap-2">
                                <Users size={18} className={c.classes.text} />
                                <span className="text-lg font-black text-white">{course.enrollment_count || 0}</span>
                            </div>
                        </div>
                    </div>

                    {/* Meta chips */}
                    <div className="flex flex-wrap items-center gap-3">
                        {[{ icon: BarChart, label: 'سطح', val: course.level },
                          { icon: Clock, label: 'زمان', val: displayHours && `${displayHours} ساعت` },
                          { icon: BookOpen, label: 'تعداد دروس', val: course.sessions && `${course.sessions} درس` }
                        ].filter(x => x.val).map(({ icon: Icon, label, val }) => (
                            <div key={label} className="flex items-center gap-2 bg-dark-lightest/80 px-4 py-2 rounded-2xl border border-purple-900/20 shadow-inner">
                                <Icon size={18} className={c.classes.text} />
                                <span className="text-sm font-bold text-slate-200">{label}: <span className="text-white font-normal">{val}</span></span>
                            </div>
                        ))}
                    </div>

                    {/* Author */}
                    <div className={`flex items-center gap-3 bg-white/[0.015] border ${c.classes.border} rounded-2xl p-4`}>
                        <div className={`w-10 h-10 rounded-full ${c.classes.bgLight} border ${c.classes.border} flex items-center justify-center`}>
                            <Users size={18} className={c.classes.text} />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">ساخته‌شده توسط</span>
                            <span className={`text-sm font-bold text-white ${isEnglish(course.author_name) ? 'ltr-content' : ''}`}>{course.author_name || 'کاربر بلو'}</span>
                        </div>
                    </div>

                    {/* Goal */}
                    {course.course_goal && (
                        <div className={`flex flex-col gap-2 bg-white/[0.015] border ${c.classes.border} rounded-2xl p-4`}>
                            <span className={`text-xs font-bold ${c.classes.text} flex items-center gap-1.5`}><Target size={16} /> هدف دوره:</span>
                            <span className={`text-sm text-slate-200 leading-relaxed ${isEnglish(course.course_goal) ? 'ltr-content' : ''}`}>{course.course_goal}</span>
                        </div>
                    )}

                    {/* Learning outcomes */}
                    {learningOutcomes.length > 0 && (
                        <div className={`bg-white/[0.015] border ${c.classes.border} rounded-2xl p-5`}>
                            <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                                <BookOpen size={16} className={c.classes.text} /> چیزهایی که یاد خواهید گرفت:
                            </h3>
                            <ul className="space-y-2">
                                {learningOutcomes.map((outcome, idx) => (
                                    <li key={idx} className={`text-sm text-slate-300 flex items-start gap-2 ${isEnglish(outcome) ? 'ltr-content' : ''}`}>
                                        <CheckCircle size={14} className={`${c.classes.text} shrink-0 mt-0.5`} />
                                        <span>{outcome}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Prerequisites */}
                    {prerequisites.length > 0 && (
                        <div className={`bg-white/[0.015] border ${c.classes.border} rounded-2xl p-5`}>
                            <h3 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
                                <Target size={16} className={c.classes.text} /> پیشنیازها:
                            </h3>
                            <ul className="space-y-2">
                                {prerequisites.map((prereq, idx) => (
                                    <li key={idx} className={`text-sm text-slate-300 flex items-start gap-2 ${isEnglish(prereq) ? 'ltr-content' : ''}`}>
                                        <span className={`${c.classes.text} shrink-0 font-bold`}>{"•"}</span>
                                        <span>{prereq}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Rate this course */}
                    <div className={`flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white/[0.015] border ${c.classes.border} rounded-2xl p-5`}>
                        <div className="flex flex-col gap-1">
                            <span className="text-sm font-bold text-white">به این دوره امتیاز دهید</span>
                            <span className="text-xs text-slate-400">تجربه خود را با دیگران به اشتراک بگذارید</span>
                        </div>
                        <StarRating
                            value={course.my_rating || 0}
                            onChange={(n) => onRate(course.id, n)}
                            size={26}
                        />
                    </div>

                    {/* Action button */}
                    <div className="mt-2 pt-6 border-t border-purple-900/20">
                        {course.is_enrolled ? (
                            <button
                                onClick={() => onOpenCourse(course)}
                                className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:brightness-110 text-white py-4 rounded-2xl font-bold flex items-center justify-center gap-3 shadow-lg shadow-green-900/20 hover:shadow-green-500/40 transition-all active:scale-[0.98]"
                            >
                                <BookOpen size={20} /> ادامه یادگیری در دوره‌های من
                            </button>
                        ) : (
                            <button
                                onClick={() => onEnroll(course)}
                                disabled={isEnrolling}
                                className={`w-full bg-gradient-to-r ${c.classes.from} ${c.classes.to} text-white py-4 rounded-2xl font-bold flex items-center justify-center gap-3 ${c.classes.shadowHover} hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-70 disabled:cursor-wait`}
                            >
                                {isEnrolling ? (
                                    <><Loader2 size={20} className="animate-spin" /> در حال ثبت‌نام...</>
                                ) : (
                                    <><Zap size={20} className="fill-current" /> ثبت‌نام در این دوره</>
                                )}
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Course Outline Roadmap ── */}
            <div className={`bg-dark-lighter border ${c.classes.border} rounded-[2.5rem] p-6 md:p-12 shadow-[0_0_60px_rgba(0,0,0,0.6)] relative overflow-hidden`}>
                <div className={`absolute top-0 right-0 w-80 h-80 ${c.classes.glow} rounded-full blur-[120px] pointer-events-none opacity-20`} />
                <div className="relative z-10 flex flex-col gap-10">
                    {/* Section header */}
                    <div className="flex items-center gap-5">
                        <div className={`p-4 rounded-3xl ${c.classes.bgLight} shadow-xl border border-white/10 backdrop-blur-md`}>
                            <BookOpen className={c.classes.text} size={28} />
                        </div>
                        <div>
                            <h3 className="text-2xl md:text-3xl font-black text-white tracking-tight">سرفصل‌های دوره</h3>
                            <div className="flex items-center gap-3 mt-2">
                                <span className="text-sm text-slate-400 font-medium">مسیر یادگیری این دوره آموزشی</span>
                                <div className="w-1 h-1 rounded-full bg-slate-600" />
                                <span className={`text-xs font-bold ${c.classes.text}`}>{items.length} درس</span>
                            </div>
                        </div>
                    </div>

                    {/* Outline */}
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-16 text-center">
                            <div className="relative w-12 h-12 mb-4">
                                <div className="absolute inset-0 border-3 border-purple-900/30 rounded-full" />
                                <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent animate-spin" />
                            </div>
                            <p className="text-slate-400 text-sm">در حال بارگذاری سرفصل‌ها...</p>
                        </div>
                    ) : (
                        <GlobalOutline items={items} sColor={c} />
                    )}
                </div>
            </div>
        </div>
    );
}
