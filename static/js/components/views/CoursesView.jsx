const { ChevronRight, Settings, BarChart, Clock, BookOpen, Trophy, Play, Pause, CheckCircle, Layout, Copy, RefreshCw, MoreVertical, ChevronLeft, Sparkles, Maximize, Send, X, Loader2, Bot, Zap, Edit2 } = window.Icons;

function CourseHero({ course, sColor, onBack, onEditCourse, onContinue }) {
    const lastId = localStorage.getItem(`last_session_${course.id}`);
    const next = (lastId && course.items.find(i => i.id == lastId)) || course.items.find(i => !i.is_completed);
    return (
        <div className="relative bg-dark-lighter/60 backdrop-blur-xl border border-purple-900/30 rounded-[2.5rem] mb-10 overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] flex flex-col">
            <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
                <div className={`absolute -top-20 -left-20 w-64 h-64 ${sColor.classes.glow} rounded-full blur-[80px]`} />
                <div className={`absolute -bottom-32 -right-32 w-80 h-80 ${sColor.classes.bgLight} rounded-full blur-[100px]`} />
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
                        <ChevronRight size={18} className="group-hover/back:translate-x-1 transition-transform" /> بازگشت به دوره‌ها
                    </button>
                    <button onClick={onEditCourse} className={`p-2.5 text-slate-400 hover:text-white bg-dark-lightest/50 rounded-xl border border-purple-900/20 hover:bg-dark-lightest ${sColor.classes.hoverBorder} transition-all`}>
                        <Settings size={20} className={sColor.classes.text} />
                    </button>
                </div>
                <div>
                    <h2 className={`text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight ${isEnglish(course.short_title || course.title) ? 'ltr-content' : ''}`}>{course.short_title || course.title}</h2>
                    <p className={`text-slate-300 text-sm md:text-base leading-relaxed max-w-4xl opacity-90 ${isEnglish(course.description) ? 'ltr-content' : ''}`}>{course.description}</p>
                </div>
                <div className="flex flex-wrap items-center gap-3 mt-2">
                    {[{ icon: BarChart, label: 'سطح', val: course.level }, { icon: Clock, label: 'زمان', val: course.hours && `${course.hours} ساعت` }, { icon: BookOpen, label: 'تعداد دروس', val: course.sessions && `${course.sessions} درس` }].filter(x => x.val).map(({ icon: Icon, label, val }) => (
                        <div key={label} className="flex items-center gap-2 bg-dark-lightest/80 px-4 py-2 rounded-2xl border border-purple-900/20 shadow-inner">
                            <Icon size={18} className={sColor.classes.text} />
                            <span className="text-sm font-bold text-slate-200">{label}: <span className="text-white font-normal">{val}</span></span>
                        </div>
                    ))}
                    {/* Total reading time for this course */}
                    {(() => {
                        const totalSecs = (course.items || []).reduce((sum, i) => sum + (i.study_time || 0), 0);
                        if (totalSecs < 60) return null;
                        const h = Math.floor(totalSecs / 3600);
                        const m = Math.floor((totalSecs % 3600) / 60);
                        const label = h > 0 ? `${h}h ${m}m مطالعه` : `${m} دقیقه مطالعه`;
                        return (
                            <div className={`flex items-center gap-2 ${sColor.classes.bgLight} px-4 py-2 rounded-2xl border ${sColor.classes.border} shadow-inner`}>
                                <Clock size={16} className={sColor.classes.text} />
                                <span className={`text-sm font-bold ${sColor.classes.text}`}>{label}</span>
                            </div>
                        );
                    })()}
                </div>
                <div className="mt-6 pt-6 border-t border-purple-900/20">
                    <div className="flex flex-col sm:flex-row justify-between items-center gap-6">
                        <div className="flex-1 w-full">
                            <div className="flex justify-between items-center mb-3">
                                <span className="text-sm font-bold text-slate-300 flex items-center gap-2"><Trophy size={18} className={course.progress === 100 ? 'text-yellow-500' : sColor.classes.text} /> میزان تسلط شما</span>
                                <span className={`text-lg font-bold text-white ${sColor.classes.bgLight} px-3 py-1 rounded-xl border border-purple-900/20 ${sColor.classes.dropShadow}`}>{Math.round(course.progress)}%</span>
                            </div>
                            <div className="w-full bg-dark-lightest/60 h-4 rounded-full overflow-hidden shadow-inner border border-purple-900/30 relative">
                                <div className={`bg-gradient-to-r ${sColor.classes.from} ${sColor.classes.to} h-full transition-all duration-1000 ease-out relative`} style={{ width: `${course.progress}%` }}>
                                    <div className="absolute top-0 right-0 bottom-0 w-20 bg-gradient-to-r from-transparent to-white/30 animate-[shimmer_2s_infinite]" />
                                </div>
                            </div>
                        </div>
                        {next ? (
                            <button onClick={() => onContinue(next)} className={`w-full sm:w-auto mt-4 sm:mt-0 bg-gradient-to-r ${sColor.classes.from} ${sColor.classes.to} text-white px-8 py-3.5 rounded-2xl flex items-center justify-center gap-3 font-bold ${sColor.classes.shadowHover} transition-all flex-shrink-0 group/continue`}>
                                <Play fill="currentColor" size={18} className="rotate-180 group-hover/continue:scale-110 transition-transform" /> ادامه یادگیری
                            </button>
                        ) : (
                            <div className="w-full sm:w-auto mt-4 sm:mt-0 bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 px-8 py-3.5 rounded-2xl flex items-center justify-center gap-3 font-bold flex-shrink-0">
                                <CheckCircle size={18} /> دوره تکمیل شد
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function ItemContent({ item, vColor, studyTimer, isSessionMenuOpen, setIsSessionMenuOpen, sessionMenuRef, onBack, onCopy, copied, onRegenerate, onComplete, prevItem, nextItem, onNavItem, loadingItemId, isTimerPaused, setIsTimerPaused, onManualTimeUpdate }) {
    const [isEditingTime, setIsEditingTime] = React.useState(false);
    const [manualMinutes, setManualMinutes] = React.useState(0);

    const handleEditTime = () => {
        const totalSecs = studyTimer;
        setManualMinutes(Math.round(totalSecs / 60));
        setIsEditingTime(true);
    };

    const saveManualTime = () => {
        onManualTimeUpdate(manualMinutes * 60, item.id);
        setIsEditingTime(false);
    };

    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between gap-4 mb-8">
                <button onClick={onBack} className="w-10 h-10 rounded-full bg-dark-lightest flex items-center justify-center text-slate-400 hover:text-white transition-colors"><ChevronRight size={20} /></button>
                
                {/* ── Modernized study timer & manual editor ── */}
                <div className={`flex items-center gap-2.5 bg-dark-lightest/30 border border-white/5 px-4 py-2 rounded-full ml-auto backdrop-blur-xl group/timer transition-all duration-500 ${isEditingTime ? 'ring-2 ring-primary/20 bg-dark-lightest/60' : ''}`} title="زمان مطالعه">
                    {!isEditingTime ? (
                        <div className="flex items-center gap-3">
                            <button onClick={() => setIsTimerPaused(!isTimerPaused)} className={`${vColor.classes.text} hover:scale-125 active:scale-95 transition-all duration-300 drop-shadow-[0_0_8px_currentColor]`}>
                                {isTimerPaused ? <Play size={13} fill="currentColor" className="rotate-180" /> : <Pause size={13} fill="currentColor" />}
                            </button>
                            
                            <div className="flex items-center gap-2" onClick={handleEditTime} role="button">
                                <div className={`w-1.5 h-1.5 rounded-full ${vColor.classes.text} ${!isTimerPaused ? 'animate-pulse shadow-[0_0_8px_currentColor]' : 'opacity-40'}`} style={{backgroundColor: 'currentColor'}} />
                                <span className={`text-[13px] font-mono font-black tracking-wider ${vColor.classes.text} transition-all group-hover/timer:scale-105`}>
                                    {(() => { 
                                        const t = studyTimer; 
                                        const h=Math.floor(t/3600),m=Math.floor((t%3600)/60),s=t%60; 
                                        return h>0?`${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`:`${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`; 
                                    })()}
                                </span>
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center gap-3 animate-in fade-in zoom-in duration-300">
                            <div className="relative flex items-center">
                                <input 
                                    type="number" 
                                    value={manualMinutes} 
                                    onChange={(e) => setManualMinutes(parseInt(e.target.value) || 0)}
                                    className="w-14 bg-transparent text-sm font-black font-mono text-white focus:outline-none text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                    autoFocus
                                />
                                <span className="absolute -top-4 left-1/2 -translate-x-1/2 text-[8px] font-black text-primary uppercase tracking-widest opacity-60">دقایق</span>
                            </div>
                            <div className="h-4 w-px bg-white/10 mx-1" />
                            <div className="flex items-center gap-1.5">
                                <button onClick={saveManualTime} className="w-6 h-6 rounded-lg bg-green-500/20 text-green-500 flex items-center justify-center hover:bg-green-500/30 transition-colors">
                                    <CheckCircle size={14} />
                                </button>
                                <button onClick={() => setIsEditingTime(false)} className="w-6 h-6 rounded-lg bg-red-500/20 text-red-500 flex items-center justify-center hover:bg-red-500/30 transition-colors">
                                    <X size={14} />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
                {item.content && (
                    <div className="relative" ref={sessionMenuRef}>
                        <button onClick={() => setIsSessionMenuOpen(o => !o)} className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isSessionMenuOpen ? 'bg-dark-lightest text-white' : 'text-slate-400 hover:text-white hover:bg-dark-lightest'}`}><MoreVertical size={20} /></button>
                        {isSessionMenuOpen && (
                            <div className="absolute left-0 top-full mt-2 w-48 bg-dark-lightest border border-purple-900/30 rounded-2xl shadow-2xl z-20 overflow-hidden backdrop-blur-xl">
                                <button onClick={() => { onCopy(); setIsSessionMenuOpen(false); }} className="w-full text-right px-4 py-3 text-sm hover:bg-white/5 flex items-center gap-3 text-slate-200 transition-colors">
                                    {copied ? <CheckCircle size={16} className="text-green-500" /> : <Copy size={16} className="text-slate-400" />} {copied ? 'کپی شد' : 'کپی متن درس'}
                                </button>
                                <button onClick={() => { onRegenerate(item.id); setIsSessionMenuOpen(false); }} className="w-full text-right px-4 py-3 text-sm hover:bg-white/5 flex items-center gap-3 text-primary transition-colors border-t border-purple-900/20">
                                    <RefreshCw size={16} /> تولید مجدد درس
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
            <h3 className={`text-2xl md:text-3xl font-bold mb-8 text-white ${isEnglish(item.title) ? 'ltr-content' : ''}`}>{item.title}</h3>
            {(!item.content || loadingItemId === item.id) ? (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                    <div className="relative w-20 h-20 mb-6">
                        <div className="absolute inset-0 border-4 border-purple-900/30 rounded-full" />
                        <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent animate-spin" />
                        <Bot className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-primary" size={24} />
                    </div>
                    <h4 className="text-xl font-bold text-white mb-2">در حال تالیف این درس...</h4>
                    <p className="text-slate-400 max-w-sm">هوش مصنوعی در حال گردآوری بهترین مطالب برای شماست.</p>
                </div>
            ) : (
                <>
                    <div className={`prose prose-invert prose-purple max-w-none prose-pre:bg-dark-lightest prose-pre:border prose-pre:border-purple-900/30 prose-p:text-slate-300 prose-headings:text-white prose-a:text-primary ${isEnglish(item.content) ? 'ltr-content' : ''}`} dangerouslySetInnerHTML={{ __html: marked.parse(item.content) }} />
                    <div className="mt-20 space-y-6">
                        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-10 border-t border-purple-900/10">
                            <div className="flex-1 w-full">
                                {prevItem && <button onClick={() => onNavItem(prevItem)} className="group flex items-center gap-3 text-slate-400 hover:text-white bg-dark-lightest/30 px-4 py-2.5 rounded-xl border border-purple-900/5 hover:border-purple-900/20 w-full sm:w-fit transition-all">
                                    <ChevronRight size={18} className="group-hover:-translate-x-1.5 transition-transform text-slate-500" /><span className="text-sm font-bold truncate max-w-[200px]">{prevItem.title}</span>
                                </button>}
                            </div>
                            <div className="flex-1 w-full flex justify-end">
                                {nextItem && <button onClick={() => onNavItem(nextItem)} className="group flex items-center gap-3 text-slate-400 hover:text-white bg-dark-lightest/30 px-4 py-2.5 rounded-xl border border-purple-900/5 hover:border-purple-900/20 w-full sm:w-fit transition-all">
                                    <span className="text-sm font-bold truncate max-w-[200px]">{nextItem.title}</span><ChevronLeft size={18} className="group-hover:translate-x-1.5 transition-transform text-slate-500" />
                                </button>}
                            </div>
                        </div>
                        <div>
                            {!item.is_completed ? (
                                <button onClick={() => onComplete(item.id)} className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-green-500/90 to-emerald-600/90 hover:from-green-500 hover:to-emerald-600 text-white py-4 rounded-2xl font-bold shadow-lg shadow-green-900/20 hover:shadow-green-500/40 transition-all group">
                                    <CheckCircle size={22} className="group-hover:scale-110 transition-transform" /> اتمام این مرحله و تایید یادگیری
                                </button>
                            ) : (
                                <div className="w-full flex items-center justify-center gap-3 bg-green-500/10 border border-green-500/20 text-green-400 py-4 rounded-2xl font-bold">
                                    <CheckCircle size={22} /> این درس را با موفقیت پشت سر گذاشتید
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function CoachSidebar({ course, viewingItem, vColor, isCoachMode, setIsCoachMode, isCoachFullScreen, setIsCoachFullScreen, isSidebarOpen, setIsSidebarOpen, coachMessages, coachInput, setCoachInput, isCoachLoading, onSendCoach, coachScrollRef, openChapters, setOpenChapters, onItemClick }) {
    return (
        <div className="bg-dark-lighter border border-purple-900/20 rounded-[2.5rem] p-6 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.7)] h-[calc(100vh-4rem)] flex flex-col relative overflow-hidden">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    {viewingItem && (
                        <button onClick={() => setIsCoachMode(m => !m)} className={`flex items-center gap-2.5 h-9 px-4 rounded-full transition-all ${isCoachMode ? 'bg-primary text-white shadow-[0_0_20px_rgba(168,85,247,0.4)]' : 'bg-dark-lightest/50 text-slate-400 hover:text-primary border border-purple-900/20'}`}>
                            <Sparkles size={18} className={isCoachMode ? 'animate-pulse' : ''} /><span className="text-xs font-bold">هوش مصنوعی</span>
                        </button>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {isCoachMode && <button onClick={() => setIsCoachFullScreen(true)} className="w-8 h-8 flex items-center justify-center bg-dark-lightest/50 hover:bg-primary/10 text-slate-400 hover:text-primary rounded-lg transition-all"><Maximize size={16} /></button>}
                    <button onClick={() => setIsSidebarOpen(false)} className="w-8 h-8 flex items-center justify-center bg-dark-lightest/50 hover:bg-red-500/10 text-slate-400 hover:text-red-400 rounded-lg transition-all"><X size={16} /></button>
                </div>
            </div>
            {!isCoachMode && (
                <div className="mb-8 pb-6 border-b border-purple-900/10">
                    <h3 className="text-xl font-bold text-white mb-4 leading-tight">{course.short_title || course.title}</h3>
                    <div className="flex justify-between text-xs mb-2 px-1"><span className={`${vColor.classes.text} font-bold`}>{Math.round(course.progress)}%</span></div>
                    <div className="w-full bg-dark-lightest/50 h-2 rounded-full overflow-hidden shadow-inner">
                        <div className={`bg-gradient-to-r ${vColor.classes.from} ${vColor.classes.to} h-full transition-all duration-700 ${vColor.classes.dropShadow}`} style={{ width: `${course.progress}%` }} />
                    </div>
                </div>
            )}
            <div className="flex-1 flex flex-col overflow-hidden relative">
                {isCoachMode ? (
                    <div className="flex-1 flex flex-col h-full absolute inset-0">
                        <div className="flex-1 overflow-y-auto pr-1 pb-4 space-y-5" ref={coachScrollRef}>
                            {coachMessages.map((msg, idx) => (
                                <div key={idx} className="flex flex-col w-full">
                                    {msg.role === 'user' ? (
                                        <div className="bg-primary/20 text-slate-100 px-4 py-3 rounded-2xl rounded-tr-sm max-w-[90%] border border-primary/20 shadow-sm ml-auto text-sm leading-relaxed">{msg.content}</div>
                                    ) : (
                                        <div className="text-slate-200 w-full text-sm leading-relaxed py-1 pr-3 border-r-2 border-primary/40">
                                            <div dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || '...') }} className={`prose prose-sm prose-invert prose-p:my-1 prose-a:text-primary prose-strong:text-white max-w-none ${isEnglish(msg.content) ? 'ltr-content' : ''}`} />
                                        </div>
                                    )}
                                </div>
                            ))}
                            {isCoachLoading && <div className={`flex items-center gap-2 pr-3 border-r-2 ${vColor.classes.border} py-2`}><Loader2 size={14} className={`${vColor.classes.text} animate-spin`} /><span className="animate-pulse text-xs text-slate-400">در حال فکر کردن...</span></div>}
                        </div>
                        <form onSubmit={(e) => { e.preventDefault(); onSendCoach(); }} className="mt-4 flex items-center relative">
                            <input type="text" value={coachInput} onChange={(e) => setCoachInput(e.target.value)} placeholder="سوال خود را بپرسید..." disabled={isCoachLoading}
                                className="w-full bg-dark-lightest/60 border border-purple-900/30 rounded-2xl py-3.5 pr-5 pl-12 text-sm text-white focus:outline-none focus:border-primary/50 transition-all placeholder:text-slate-500" />
                            <button type="submit" disabled={isCoachLoading || !coachInput.trim()} className="absolute left-1.5 w-9 h-9 rounded-xl bg-primary/10 hover:bg-primary text-primary hover:text-white transition-all flex items-center justify-center disabled:opacity-0">
                                <Send size={16} className="rotate-180" />
                            </button>
                        </form>
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col gap-2.5 overflow-y-auto pr-1 pb-4 h-full absolute inset-0">
                        <ChapterNav course={course} viewingItem={viewingItem} vColor={vColor} openChapters={openChapters} setOpenChapters={setOpenChapters} onItemClick={onItemClick} />
                    </div>
                )}
            </div>
        </div>
    );
}

function CoursesView({ courses, selectedCourse, viewingItem, setViewingItem, onSelectCourse, onBack, onEditCourse, onDeleteCourse, onGenerateMicro, onGenerateItem, onCompleteItem, onCopyContent, onSendCoach, activeMenu, setActiveMenu, menuRef, sessionMenuRef, isSessionMenuOpen, setIsSessionMenuOpen, copied, isSidebarOpen, setIsSidebarOpen, isCoachMode, setIsCoachMode, isCoachFullScreen, setIsCoachFullScreen, coachMessages, coachInput, setCoachInput, isCoachLoading, coachScrollRef, openChapters, setOpenChapters, studyTimer, loadingItemId, sidebarRatio, isDragging, startDrag, contentRef, isTimerPaused, setIsTimerPaused, onManualTimeUpdate }) {
    if (!selectedCourse) return (
        <>
            <h2 className="text-2xl font-bold mb-8 flex items-center gap-3 text-white"><Layout className="text-primary" size={28} /> دوره‌های شما</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {courses.map(course => <CourseCard key={course.id} course={course} onSelect={onSelectCourse} onEdit={onEditCourse} onDelete={onDeleteCourse} activeMenu={activeMenu} setActiveMenu={setActiveMenu} menuRef={menuRef} />)}
            </div>
        </>
    );

    const sColor = getCourseColor(selectedCourse.color);
    const vColor = sColor;
    const items = selectedCourse.items || [];
    const curIdx = viewingItem ? items.findIndex(i => i.id === viewingItem.id) : -1;
    const prevItem = curIdx > 0 ? items[curIdx - 1] : null;
    const nextItem = curIdx !== -1 && curIdx < items.length - 1 ? items[curIdx + 1] : null;
    const navItem = (item) => item.content ? setViewingItem(item) : onGenerateItem(item.id);

    return (
        <div className="flex flex-col gap-8">
            {!viewingItem && <CourseHero course={selectedCourse} sColor={sColor} onBack={onBack} onEditCourse={() => onEditCourse(selectedCourse)} onContinue={navItem} />}
            {viewingItem ? (
                <div className="flex flex-col-reverse lg:flex-row gap-3 relative items-start w-full" ref={contentRef}>
                    <div className={`bg-dark-lighter border ${vColor.classes.border} rounded-[2rem] p-6 md:p-10 shadow-[0_0_40px_rgba(0,0,0,0.5)] min-h-[60vh]`}
                        style={{ width: isSidebarOpen ? (window.innerWidth >= 1024 ? `${100 - sidebarRatio}%` : '100%') : '100%', transition: isDragging ? 'none' : 'width 0.3s ease-in-out' }}>
                        <ItemContent 
                            item={viewingItem} vColor={vColor} studyTimer={studyTimer} 
                            isSessionMenuOpen={isSessionMenuOpen} setIsSessionMenuOpen={setIsSessionMenuOpen} 
                            sessionMenuRef={sessionMenuRef} onBack={() => setViewingItem(null)} 
                            onCopy={onCopyContent} copied={copied} onRegenerate={onGenerateItem} 
                            onComplete={onCompleteItem} prevItem={prevItem} nextItem={nextItem} 
                            onNavItem={navItem} loadingItemId={loadingItemId}
                            isTimerPaused={isTimerPaused} setIsTimerPaused={setIsTimerPaused}
                            onManualTimeUpdate={onManualTimeUpdate}
                        />
                    </div>
                    {isSidebarOpen && (
                        <div className="w-4 cursor-col-resize hidden lg:flex items-center justify-center group self-stretch z-20 hover:bg-primary/5 transition-all" onMouseDown={startDrag}>
                            <div className="w-1.5 h-16 bg-primary/40 rounded-full group-hover:bg-primary transition-all opacity-0 group-hover:opacity-100" />
                        </div>
                    )}
                    <div className={`sticky top-8 ${isSidebarOpen ? 'opacity-100' : 'w-0 opacity-0 hidden lg:block'}`}
                        style={{ width: isSidebarOpen ? (window.innerWidth >= 1024 ? `${sidebarRatio}%` : '100%') : '0%', transition: isDragging ? 'none' : 'width 0.3s ease-in-out, opacity 0.3s ease-in-out' }}>
                        <CoachSidebar course={selectedCourse} viewingItem={viewingItem} vColor={vColor} isCoachMode={isCoachMode} setIsCoachMode={setIsCoachMode} isCoachFullScreen={isCoachFullScreen} setIsCoachFullScreen={setIsCoachFullScreen} isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} coachMessages={coachMessages} coachInput={coachInput} setCoachInput={setCoachInput} isCoachLoading={isCoachLoading} onSendCoach={onSendCoach} coachScrollRef={coachScrollRef} openChapters={openChapters} setOpenChapters={setOpenChapters} onItemClick={navItem} />
                    </div>
                    {!isSidebarOpen && (
                        <button onClick={() => setIsSidebarOpen(true)} className={`fixed left-0 top-1/2 -translate-y-1/2 bg-dark-lighter border ${vColor.classes.border} border-l-0 p-2 py-6 rounded-r-2xl shadow-[0_0_30px_rgba(0,0,0,0.5)] ${vColor.classes.text} transition-all z-40 group`}>
                            <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </button>
                    )}
                </div>
            ) : (
                <CourseRoadmap course={selectedCourse} sColor={sColor} onItemClick={navItem} viewingItem={viewingItem} />
            )}
        </div>
    );
}
