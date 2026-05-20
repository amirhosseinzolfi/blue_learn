const {
    BookOpen, Layout, Zap, BarChart, Settings, Plus
} = window.Icons;

function Sidebar({ currentView, setCurrentView, setSelectedCourse, openChatModal }) {
    const navItems = [
        { view: 'courses', icon: Layout, label: 'دوره\u200cها' },
        { view: 'micro', icon: Zap, label: 'میکرو دوره\u200cها' },
        { view: 'progress', icon: BarChart, label: 'پیشرفت' },
        { view: 'settings', icon: Settings, label: 'تنظیمات' },
    ];

    const navigate = (view) => { setCurrentView(view); setSelectedCourse(null); };

    return (
        <>
            {/* Desktop sidebar */}
            <div className="hidden md:block w-[72px] shrink-0 z-50 relative">
                <aside className="group fixed top-[110px] bottom-[110px] right-4 w-[72px] hover:w-[218px] bg-dark-lighter/95 backdrop-blur-xl border border-white/[0.06] flex flex-col shadow-[0_8px_40px_rgba(0,0,0,0.6),inset_0_1px_0_rgba(255,255,255,0.04)] rounded-[1.75rem] transition-[width] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] overflow-hidden">
                    {/* Logo */}
                    <div className="flex items-center h-16 px-[18px] shrink-0 border-b border-white/[0.05]">
                        <div className="w-8 h-8 shrink-0 flex items-center justify-center rounded-xl bg-primary/15 border border-primary/20 shadow-[0_0_12px_rgba(168,85,247,0.15)]">
                            <BookOpen className="text-primary" size={15} />
                        </div>
                        <span className="mr-3 text-[15px] font-bold bg-gradient-to-l from-purple-300 to-indigo-300 bg-clip-text text-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap tracking-wide">
                            بلو لرن
                        </span>
                    </div>

                    {/* Nav */}
                    <nav className="flex-1 flex flex-col gap-0.5 p-2 pt-2.5">
                        {navItems.map(({ view, icon: Icon, label }) => (
                            <button
                                key={view}
                                onClick={() => navigate(view)}
                                title={label}
                                className={`relative flex items-center h-10 rounded-xl transition-all duration-200 group/item overflow-hidden ${currentView === view ? 'bg-primary/15 text-primary' : 'text-slate-500 hover:text-slate-200 hover:bg-white/[0.05]'}`}
                            >
                                {currentView === view && (
                                    <span className="absolute right-0 top-1/2 -translate-y-1/2 w-[3px] h-4 bg-primary rounded-l-full shadow-[0_0_6px_rgba(168,85,247,0.7)]" />
                                )}
                                <span className="flex items-center justify-center w-[52px] shrink-0">
                                    <Icon size={17} className={`transition-transform duration-200 ${currentView === view ? '' : 'group-hover/item:scale-110'}`} />
                                </span>
                                <span className="text-[15px] font-bold opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pr-1 leading-none">{label}</span>
                            </button>
                        ))}
                    </nav>

                    {/* New course button */}
                    <div className="p-2 pb-2.5 shrink-0 border-t border-white/[0.04]">
                        <button
                            onClick={openChatModal}
                            title="دوره جدید"
                            className="w-full h-10 flex items-center rounded-xl bg-primary/20 hover:bg-primary/30 border border-primary/25 hover:border-primary/50 text-primary transition-all duration-200 group/btn overflow-hidden"
                        >
                            <span className="flex items-center justify-center w-[52px] shrink-0">
                                <Plus size={17} className="group-hover/btn:rotate-90 transition-transform duration-300" />
                            </span>
                            <span className="text-[15px] font-bold opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pr-1">دوره جدید</span>
                        </button>
                    </div>
                </aside>
            </div>

            {/* Mobile header */}
            <header className="md:hidden flex justify-between items-center px-4 py-2.5 border-b border-white/[0.05] bg-dark-lighter/90 backdrop-blur-xl sticky top-0 z-20">
                <div className="flex items-center gap-2">
                    <div className="w-7 h-7 flex items-center justify-center rounded-lg bg-primary/15 border border-primary/20">
                        <BookOpen size={13} className="text-primary" />
                    </div>
                    <span className="text-sm font-bold bg-gradient-to-l from-purple-300 to-indigo-300 bg-clip-text text-transparent">بلو لرن</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="flex items-center gap-0.5 bg-dark-lightest/70 p-1 rounded-xl border border-white/[0.05]">
                        {navItems.map(({ view, icon: Icon }) => (
                            <button
                                key={view}
                                onClick={() => navigate(view)}
                                className={`p-2 rounded-lg transition-all duration-200 ${currentView === view ? 'bg-primary/20 text-primary' : 'text-slate-500 hover:text-slate-300'}`}
                            >
                                <Icon size={16} />
                            </button>
                        ))}
                    </div>
                    <button
                        onClick={openChatModal}
                        className="mr-1 p-2 rounded-xl text-primary bg-primary/15 hover:bg-primary/25 border border-primary/20 transition-all duration-200"
                    >
                        <Plus size={16} />
                    </button>
                </div>
            </header>
        </>
    );
}
