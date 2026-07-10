// Course list grid card
function CourseCard({ course, onSelect, onEdit, onDelete, onTogglePublish, onCopyCourse, activeMenu, setActiveMenu, menuRef }) {
    const { Trophy, MoreVertical, Settings, Trash2, BarChart, BookOpen, Globe, X, Copy } = window.Icons;
    const c = getCourseColor(course.color);
    return (
        <div onClick={() => onSelect(course.id)}
            className={`bg-dark-lighter border ${c.classes.border} p-7 rounded-[2rem] cursor-pointer ${c.classes.hoverBorder} transition-all duration-300 group relative shadow-lg shadow-black/20 ${c.classes.shadowHover}`}>
            {course.cover_image && (
                <div className="w-full h-32 md:h-40 rounded-[1.5rem] mb-5 overflow-hidden relative shadow-inner">
                    <img src={course.cover_image} alt={course.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out" />
                    <div className="absolute inset-0 bg-gradient-to-t from-dark-lighter via-dark-lighter/20 to-transparent" />
                </div>
            )}
            {course.is_published && (
                <div className="absolute top-4 left-4 z-10 flex items-center gap-1.5 bg-primary/20 border border-primary/30 backdrop-blur-md px-2.5 py-1 rounded-full text-[10px] font-bold text-primary">
                    <Globe size={11} /> منتشر شده
                </div>
            )}
            <div className="flex justify-between items-start mb-4">
                <h3 className={`text-xl font-bold ${c.classes.hoverText} transition-colors pr-2 text-slate-100 flex-1 ${isEnglish(course.short_title || course.title) ? 'ltr-content' : ''}`}>
                    {course.short_title || course.title}
                </h3>
                <div className="flex items-center gap-2 relative z-10">
                    <Trophy className={course.progress === 100 ? 'text-yellow-500 drop-shadow-[0_0_8px_rgba(234,179,8,0.5)]' : 'text-slate-600'} size={22} />
                    <div className="relative" ref={activeMenu === course.id ? menuRef : null}>
                        <button onClick={(e) => { e.stopPropagation(); setActiveMenu(activeMenu === course.id ? null : course.id); }}
                            className="text-slate-500 hover:text-white p-1.5 rounded-full hover:bg-dark-lightest transition-colors">
                            <MoreVertical size={18} />
                        </button>
                        {activeMenu === course.id && (
                            <div className="absolute left-0 mt-2 w-48 bg-dark-lightest border border-purple-900/30 rounded-2xl shadow-2xl shadow-black/50 z-20 overflow-hidden backdrop-blur-xl">
                                <button onClick={(e) => { e.stopPropagation(); onEdit(course); }}
                                    className="w-full text-right px-4 py-3 text-sm hover:bg-white/5 flex items-center gap-3 text-slate-200 transition-colors">
                                    <Settings size={16} className={c.classes.text} /> تنظیمات دوره
                                </button>
                                <button onClick={(e) => { e.stopPropagation(); onTogglePublish(course); }}
                                    className="w-full text-right px-4 py-3 text-sm hover:bg-white/5 flex items-center gap-3 text-slate-200 transition-colors border-t border-purple-900/20">
                                    {course.is_published
                                        ? <><X size={16} className="text-slate-400" /> لغو انتشار عمومی</>
                                        : <><Globe size={16} className={c.classes.text} /> انتشار عمومی دوره</>
                                    }
                                </button>
                                <button onClick={(e) => { e.stopPropagation(); onCopyCourse(course); setActiveMenu(null); }}
                                    className="w-full text-right px-4 py-3 text-sm hover:bg-white/5 flex items-center gap-3 text-slate-200 transition-colors border-t border-purple-900/20">
                                    <Copy size={16} className={c.classes.text} /> کپی محتوای دوره
                                </button>
                                <button onClick={(e) => onDelete(course.id, e)}
                                    className="w-full text-right px-4 py-3 text-sm hover:bg-red-500/10 flex items-center gap-3 text-red-400 transition-colors border-t border-purple-900/20">
                                    <Trash2 size={16} /> حذف دوره
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            <div className="w-full bg-dark-lightest/50 h-2 rounded-full overflow-hidden shadow-inner">
                <div className={`bg-gradient-to-r ${c.classes.from} ${c.classes.to} h-full transition-all duration-700 ease-out ${c.classes.dropShadow}`} style={{ width: `${course.progress}%` }} />
            </div>
            <div className="flex justify-between items-center mt-3 pr-1">
                <p className="text-xs text-slate-400 font-medium">{Math.round(course.progress)}% تکمیل شده</p>
                <div className="flex gap-3 text-[10px] text-slate-500 font-medium">
                    {course.level && <span className="flex items-center gap-1.5"><BarChart size={12} /> {course.level}</span>}
                    {course.sessions && <span className="flex items-center gap-1.5"><BookOpen size={12} /> {course.sessions} درس</span>}
                </div>
            </div>
        </div>
    );
}
