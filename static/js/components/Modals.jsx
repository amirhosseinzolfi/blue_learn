const { useState, useRef } = React;
const {
    Bot, X, Send, Loader2, CheckCircle,
    Sparkles, Minimize, Settings, Plus, Edit2,
    Image, Palette
} = window.Icons;

// ─── Blue AI Course Generator Chat Modal ───────────────────────────────────
function ChatModal({ messages, input, setInput, isLoading, onSend, onClose, pendingCourseData, onAcceptCourse }) {
    const scrollRef = useRef(null);

    React.useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages, isLoading]);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-dark/95 backdrop-blur-xl p-4">
            <div className="w-full max-w-4xl h-full max-h-[90vh] flex flex-col bg-dark-lighter border border-purple-500/20 rounded-[2.5rem] shadow-[0_0_80px_rgba(168,85,247,0.15)] overflow-hidden relative">
                <button onClick={onClose} className="absolute top-6 left-6 z-10 w-12 h-12 rounded-full bg-dark-lightest/80 flex items-center justify-center text-slate-400 hover:bg-red-500/20 hover:text-red-400 transition-all backdrop-blur-sm">
                    <X size={24} />
                </button>

                <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 scroll-smooth pt-20" ref={scrollRef}>
                    <div className="text-center mb-8">
                        <div className="w-20 h-20 mx-auto rounded-full bg-primary/20 flex items-center justify-center text-primary border border-primary/20 shadow-[0_0_30px_rgba(168,85,247,0.3)] mb-4">
                            <Bot size={40} className="animate-pulse" />
                        </div>
                        <h2 className="text-3xl font-bold text-white tracking-tight">Blue</h2>
                        <p className="text-sm text-primary font-medium mt-2">معمار هوشمند آموزش شما</p>
                    </div>

                    {messages.map((msg, idx) => (
                        <div key={idx} className="flex flex-col w-full">
                            {msg.role === 'user' ? (
                                <div className="bg-primary/20 text-slate-100 px-8 py-5 rounded-[2rem] rounded-tr-sm max-w-[80%] border border-primary/20 shadow-lg ml-auto text-xl leading-relaxed">
                                    {msg.content}
                                </div>
                            ) : (
                                <div className="text-slate-200 w-full text-lg leading-relaxed py-4 pr-6 border-r-[3px] border-primary/40">
                                    <div dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || '...') }} className={`prose prose-invert prose-purple max-w-none prose-p:text-slate-300 prose-headings:text-white prose-a:text-primary ${isEnglish(msg.content) ? 'ltr-content' : ''}`} />
                                    {idx === messages.length - 1 && pendingCourseData && (
                                        <div className="mt-8">
                                            <button onClick={onAcceptCourse} className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-3 text-lg shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.5)] transition-all hover:scale-105">
                                                <CheckCircle size={24} /> تایید و ساخت دوره
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-center gap-4 pr-6 border-r-[3px] border-primary/40 py-4">
                            <Loader2 size={28} className="text-primary animate-spin" />
                            <span className="animate-pulse text-xl text-slate-400">بلو در حال فکر کردن...</span>
                        </div>
                    )}
                </div>

                <div className="p-6 md:p-8 bg-gradient-to-t from-dark-lighter via-dark-lighter to-transparent shrink-0">
                    <form onSubmit={(e) => { e.preventDefault(); onSend(); }} className="flex items-center relative max-w-3xl mx-auto">
                        <input
                            type="text" value={input} onChange={(e) => setInput(e.target.value)}
                            placeholder={pendingCourseData ? 'یا تغییرات مورد نظرتان را بنویسید...' : 'پاسخ خود را برای بلو بنویسید...'}
                            className="w-full bg-dark-lightest/80 backdrop-blur-md border border-purple-900/50 rounded-[2rem] py-5 pl-20 pr-8 text-lg text-white focus:outline-none focus:border-primary/80 focus:ring-1 focus:ring-primary/50 transition-all shadow-inner placeholder:text-slate-500"
                            disabled={isLoading} autoFocus
                        />
                        <button type="submit" disabled={isLoading || !input.trim()} className="absolute left-3 top-3 bottom-3 w-14 rounded-[1.5rem] bg-primary/20 hover:bg-primary text-primary hover:text-white transition-all flex items-center justify-center disabled:opacity-0 disabled:scale-90">
                            <Send size={24} className="rotate-180" />
                        </button>
                    </form>
                    <p className="text-center text-xs text-slate-500 mt-4 font-mono font-medium">Powered by Blue AI Assistant</p>
                </div>
            </div>
        </div>
    );
}

// ─── Full-Screen Coach Chat Modal ──────────────────────────────────────────
function CoachFullScreenModal({ messages, input, setInput, isLoading, onSend, onMinimize, onClose, viewingItem, courseColor }) {
    const scrollRef = useRef(null);
    const vColor = courseColor;

    React.useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages, isLoading]);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-dark/95 backdrop-blur-xl p-4">
            <div className="w-full max-w-4xl h-full max-h-[90vh] flex flex-col bg-dark-lighter border border-purple-500/20 rounded-[2.5rem] shadow-[0_0_80px_rgba(168,85,247,0.15)] overflow-hidden">
                <div className="p-6 md:p-8 border-b border-purple-900/30 flex justify-between items-center bg-dark-lighter shrink-0">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary border border-primary/20 shadow-[0_0_20px_rgba(168,85,247,0.2)]">
                            <Sparkles size={24} className="animate-pulse" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-white">دستیار هوشمند درس</h3>
                            <p className="text-xs text-primary font-medium mt-1">{viewingItem?.title}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button onClick={onMinimize} className="w-12 h-12 rounded-full bg-dark-lightest flex items-center justify-center text-slate-400 hover:text-primary hover:bg-primary/20 transition-all">
                            <Minimize size={24} />
                        </button>
                        <button onClick={onClose} className="w-12 h-12 rounded-full bg-dark-lightest flex items-center justify-center text-slate-400 hover:text-red-400 hover:bg-red-500/20 transition-all">
                            <X size={24} />
                        </button>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 scroll-smooth" ref={scrollRef}>
                    {messages.map((msg, idx) => (
                        <div key={idx} className="flex flex-col w-full">
                            {msg.role === 'user' ? (
                                <div className={`bg-dark-lightest/50 text-slate-100 px-8 py-5 rounded-[2rem] rounded-tr-sm max-w-[80%] border ${vColor.classes.border} shadow-lg ml-auto text-xl leading-relaxed`}>
                                    {msg.content}
                                </div>
                            ) : (
                                <div className={`text-slate-200 w-full text-lg leading-relaxed py-4 pr-6 border-r-[3px] ${vColor.classes.border}`}>
                                    <div dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || '...') }} className={`prose prose-invert max-w-none prose-p:text-slate-300 ${isEnglish(msg.content) ? 'ltr-content' : ''}`} />
                                </div>
                            )}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-center gap-4 pr-6 border-r-[3px] border-primary/40 py-4">
                            <Loader2 size={28} className="text-primary animate-spin" />
                            <span className="animate-pulse text-xl text-slate-400">در حال فکر کردن...</span>
                        </div>
                    )}
                </div>

                <div className="p-6 md:p-10 bg-dark-lighter border-t border-purple-900/30 shrink-0">
                    <form onSubmit={(e) => { e.preventDefault(); onSend(); }} className="flex gap-4 relative max-w-4xl mx-auto">
                        <input
                            type="text" value={input} onChange={(e) => setInput(e.target.value)}
                            placeholder="سوال خود را بپرسید..."
                            className="flex-1 bg-dark-lightest border border-purple-900/50 rounded-3xl px-8 py-6 pr-20 text-xl text-white focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-2xl shadow-black/50"
                            disabled={isLoading}
                        />
                        <button type="submit" disabled={isLoading || !input.trim()} className={`absolute right-3 top-3 bottom-3 bg-gradient-to-r ${vColor.classes.from} ${vColor.classes.to} hover:brightness-110 disabled:opacity-50 text-white w-16 rounded-2xl transition-all flex items-center justify-center shadow-xl`}>
                            <Send size={28} className="rotate-180" />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}

// ─── Course Settings Modal ─────────────────────────────────────────────────
function CourseSettingsModal({ course, form, setForm, onSave, onClose, loading, coverInputRef }) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-dark/80 backdrop-blur-md p-4" onClick={onClose}>
            <div className="bg-dark-lighter w-full max-w-xl rounded-[2rem] border border-purple-900/30 overflow-hidden shadow-2xl" onClick={e => e.stopPropagation()}>
                <div className="p-6 border-b border-purple-900/30 flex justify-between items-center bg-dark-lightest/50">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <Settings size={20} className="text-primary" /> تنظیمات دوره
                    </h3>
                    <button onClick={onClose} className="text-slate-400 hover:text-white p-2 rounded-full hover:bg-white/5 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={onSave} className="p-6 flex flex-col gap-6">
                    {/* Title */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">نام دوره</label>
                        <input
                            type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required
                            className="w-full bg-dark-lightest border border-purple-900/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                        />
                    </div>

                    {/* Color */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                            <Palette size={16} /> رنگ اصلی دوره
                        </label>
                        <div className="flex flex-wrap gap-3">
                            {COURSE_COLORS.map(color => (
                                <button
                                    key={color.name} type="button"
                                    onClick={() => setForm({ ...form, color: color.name })}
                                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${form.color === color.name ? 'ring-2 ring-offset-2 ring-offset-dark-lighter scale-110 shadow-lg' : 'hover:scale-105 opacity-70 hover:opacity-100'}`}
                                    style={{ backgroundColor: color.hex, '--tw-ring-color': color.hex }}
                                    title={color.label}
                                >
                                    {form.color === color.name && <CheckCircle size={20} className="text-white drop-shadow-md" />}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Cover image */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                            <Image size={16} /> تصویر کاور
                        </label>
                        <div className="flex items-center gap-4">
                            {form.preview_image ? (
                                <div className="w-24 h-24 rounded-xl overflow-hidden relative border border-purple-900/30 group shrink-0">
                                    <img src={form.preview_image} alt="Preview" className="w-full h-full object-cover" />
                                    <div className="absolute inset-0 bg-dark/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer" onClick={() => coverInputRef.current?.click()}>
                                        <Edit2 size={20} className="text-white" />
                                    </div>
                                </div>
                            ) : (
                                <button type="button" onClick={() => coverInputRef.current?.click()} className="w-24 h-24 shrink-0 rounded-xl border-2 border-dashed border-purple-900/50 flex flex-col items-center justify-center text-slate-500 hover:text-primary hover:border-primary/50 hover:bg-primary/5 transition-all">
                                    <Plus size={24} />
                                    <span className="text-xs mt-1">انتخاب</span>
                                </button>
                            )}
                            <div className="flex-1">
                                <input
                                    type="file" ref={coverInputRef} accept="image/*" className="hidden"
                                    onChange={(e) => {
                                        const file = e.target.files?.[0];
                                        if (file) setForm({ ...form, cover_image: file, preview_image: URL.createObjectURL(file) });
                                    }}
                                />
                                <p className="text-xs text-slate-400 mb-2 leading-relaxed">یک تصویر زیبا برای کاور دوره خود انتخاب کنید.</p>
                                {form.preview_image && (
                                    <button type="button" onClick={() => setForm({ ...form, cover_image: null, preview_image: null })} className="text-xs text-red-400 hover:text-red-300 transition-colors">حذف تصویر فعلی</button>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end gap-3 mt-2 pt-6 border-t border-purple-900/30">
                        <button type="button" onClick={onClose} className="px-5 py-2.5 rounded-xl text-slate-300 hover:bg-white/5 transition-colors font-medium">انصراف</button>
                        <button type="submit" disabled={loading} className="bg-gradient-to-r from-primary to-indigo-600 hover:brightness-110 text-white px-6 py-2.5 rounded-xl flex items-center gap-2 font-bold shadow-[0_0_20px_rgba(168,85,247,0.3)] transition-all disabled:opacity-50">
                            {loading ? <Loader2 size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                            ذخیره تغییرات
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
