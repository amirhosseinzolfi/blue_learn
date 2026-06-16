const { useState, useRef } = React;
const {
    Bot, X, Send, Loader2, CheckCircle,
    Sparkles, Minimize, Settings, Plus, Edit2,
    Image, Palette, BarChart, Clock, BookOpen
} = window.Icons;

// ─── Blue AI Course Generator Chat Modal ───────────────────────────────────
// ─── Custom SVG Icons for ChatModal ───────────────────────────────────────
const SlidersIcon = ({ size = 18, className = '', ...props }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
        <line x1="4" y1="21" x2="4" y2="14" />
        <line x1="4" y1="10" x2="4" y2="3" />
        <line x1="12" y1="21" x2="12" y2="12" />
        <line x1="12" y1="8" x2="12" y2="3" />
        <line x1="20" y1="21" x2="20" y2="16" />
        <line x1="20" y1="12" x2="20" y2="3" />
        <line x1="1" y1="14" x2="7" y2="14" />
        <line x1="9" y1="8" x2="15" y2="8" />
        <line x1="17" y1="16" x2="23" y2="16" />
    </svg>
);

const MicIcon = ({ size = 20, className = '', ...props }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
        <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
        <line x1="12" y1="19" x2="12" y2="23"/>
        <line x1="8" y1="23" x2="16" y2="23"/>
    </svg>
);

const PaperclipIcon = ({ size = 20, className = '', ...props }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
        <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
    </svg>
);

const ArrowLeftIcon = ({ size = 20, className = '', ...props }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
        <line x1="19" y1="12" x2="5" y2="12" />
        <polyline points="12 19 5 12 12 5" />
    </svg>
);


function ChatModal({ 
    messages, input, setInput, isLoading, onSend, onClose, pendingCourseData, onAcceptCourse, autoGenerateSessionCovers,
    level, setLevel, durationSessions, setDurationSessions, learningStyle, setLearningStyle,
    attachedFiles, setAttachedFiles
}) {
    const scrollRef = useRef(null);
    const prevLenRef = useRef(messages.length);
    const fileInputRef = useRef(null);
    
    // UI state
    const [isPrefsOpen, setIsPrefsOpen] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [levelOpen, setLevelOpen] = useState(false);
    const [styleOpen, setStyleOpen] = useState(false);
    
    // Refs for recording
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const timerRef = useRef(null);

    React.useEffect(() => {
        const container = scrollRef.current;
        if (container) {
            const isNewMessage = messages.length > prevLenRef.current;
            const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 120;
            if (isNewMessage || isNearBottom || isLoading) {
                container.scrollTop = container.scrollHeight;
            }
        }
        prevLenRef.current = messages.length;
    }, [messages, isLoading]);

    // Cleanup recording timer on unmount
    React.useEffect(() => {
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, []);

    // File Selector handler
    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files || []);
        files.forEach(file => {
            const reader = new FileReader();
            reader.onloadend = () => {
                const type = file.type.startsWith('image/') ? 'image' : 'audio';
                setAttachedFiles(prev => [
                    ...prev,
                    { id: Date.now() + Math.random(), name: file.name, type: type, data: reader.result }
                ]);
            };
            reader.readAsDataURL(file);
        });
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const removeAttachedFile = (id) => {
        setAttachedFiles(prev => prev.filter(f => f.id !== id));
    };

    // Microphone Recording handlers
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);
            audioChunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    audioChunksRef.current.push(e.data);
                }
            };

            mediaRecorderRef.current.onstop = () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/mp3' });
                const reader = new FileReader();
                reader.onloadend = () => {
                    setAttachedFiles(prev => [
                        ...prev,
                        { id: Date.now() + Math.random(), name: `صدای ضبط‌شده (${recordingTime} ثانیه).mp3`, type: 'audio', data: reader.result }
                    ]);
                };
                reader.readAsDataURL(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
            setRecordingTime(0);

            timerRef.current = setInterval(() => {
                setRecordingTime(prev => prev + 1);
            }, 1000);

        } catch (err) {
            console.error("Recording error:", err);
            alert("امکان دسترسی به میکروفون وجود ندارد. لطفا مجوزهای دسترسی را بررسی نمایید.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-dark/90 backdrop-blur-md p-4">
            <div className="w-full max-w-4xl h-full max-h-[90vh] flex flex-col bg-dark-lighter border border-purple-500/15 rounded-3xl shadow-[0_15px_50px_rgba(0,0,0,0.5)] overflow-hidden relative">
                
                {/* Header Controls (Minimal Close Button on Left/Right) */}
                <div className="absolute top-4 left-4 z-20">
                    <button 
                        onClick={onClose} 
                        className="w-10 h-10 rounded-xl bg-dark-lightest/40 flex items-center justify-center text-slate-400 hover:bg-red-500/20 hover:text-red-400 transition-all backdrop-blur-sm border border-purple-500/5"
                        title="بستن"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Main scrollable area */}
                <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 scroll-smooth pt-12" ref={scrollRef}>
                    
                    {/* Logo Intro */}
                    <div className="text-center mb-8 mt-4">
                        <div className="w-14 h-14 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20 shadow-[0_0_20px_rgba(168,85,247,0.15)] mb-3">
                            <Bot size={28} className="animate-pulse" />
                        </div>
                        <h2 className="text-xl font-bold text-white tracking-tight">بلو</h2>
                        <p className="text-xs text-primary font-medium mt-1">معمار هوشمند آموزش شخصی‌سازی شده شما</p>
                    </div>

                    {/* Messages list */}
                    {messages.map((msg, idx) => (
                        <div key={idx} className="flex flex-col w-full">
                            {msg.role === 'user' ? (
                                <div className="bg-primary/10 text-slate-200 px-6 py-3.5 rounded-2xl rounded-tr-none max-w-[75%] border border-primary/15 shadow-sm ml-auto text-sm leading-relaxed mb-6">
                                    
                                    {/* Text Content */}
                                    {msg.content && <p className="whitespace-pre-line">{msg.content}</p>}
                                    
                                    {/* Visual files previews */}
                                    {(msg.images?.length > 0 || msg.audio?.length > 0) && (
                                        <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-primary/10">
                                            {msg.images?.map((img, i) => (
                                                <img key={i} src={img} className="w-16 h-16 object-cover rounded-lg border border-white/10" />
                                            ))}
                                            {msg.audio?.map((aud, i) => (
                                                <div key={i} className="flex items-center gap-1.5 bg-dark-lighter/50 px-2.5 py-1 rounded-lg text-[10px] text-slate-300">
                                                    <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                                                    <span>صوت پیوست</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-slate-300 w-full text-sm leading-relaxed py-4 pr-5 border-r-[3px] border-primary/40 mb-6">
                                    <div 
                                        dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || '...') }} 
                                        className={`prose prose-invert prose-purple max-w-none prose-p:text-slate-300 prose-p:my-1.5 prose-headings:text-white prose-a:text-primary text-sm ${isEnglish(msg.content) ? 'ltr-content' : ''}`} 
                                    />
                                    
                                    {idx === messages.length - 1 && pendingCourseData && (
                                        <div className="mt-4 flex flex-col gap-4">
                                            <button 
                                                onClick={() => onAcceptCourse(autoGenerateSessionCovers)} 
                                                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-5 py-2.5 rounded-xl font-bold flex items-center gap-2 text-xs shadow-md transition-all hover:scale-103 w-fit"
                                            >
                                                <CheckCircle size={16} /> تایید و ساخت دوره
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-center gap-3 pr-4 border-r-2 border-primary/20 py-2">
                            <Loader2 size={20} className="text-primary animate-spin" />
                            <span className="animate-pulse text-xs text-slate-400">بلو در حال فکر کردن...</span>
                        </div>
                    )}
                </div>

                {/* Footer Input Area */}
                <div className="p-4 md:p-6 bg-gradient-to-t from-dark-lighter via-dark-lighter to-transparent shrink-0">
                    <form 
                        onSubmit={(e) => { e.preventDefault(); onSend(); }} 
                        className="flex flex-col max-w-3xl mx-auto w-full"
                    >
                        {/* Course preferences/options row directly above the input capsule */}
                        <div className="flex flex-wrap gap-2 mb-3 justify-start px-1 select-none">

                            {/* ── Level Selector (custom popup) ── */}
                            <div className="relative">
                                <button
                                    type="button"
                                    onClick={() => { setLevelOpen(o => !o); setStyleOpen(false); }}
                                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                                        level !== 'default'
                                            ? 'bg-primary/15 border-primary/40 text-primary'
                                            : 'bg-purple-900/20 border-purple-500/15 text-slate-300 hover:border-primary/30 hover:text-slate-100'
                                    }`}
                                >
                                    <BarChart size={13} className="shrink-0" />
                                    <span>سطح دوره: <span className="font-bold">{{
                                        default: 'هوشمند', beginner: 'مقدماتی',
                                        intermediate: 'متوسط', expert: 'پیشرفته', high_expert: 'فوق تخصصی'
                                    }[level]}</span></span>
                                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-200 ${levelOpen ? 'rotate-180' : ''}`}><polyline points="6 9 12 15 18 9"/></svg>
                                </button>
                                {levelOpen && (
                                    <div className="absolute bottom-full mb-2 right-0 z-50 min-w-[160px] bg-[#1a1525] border border-purple-500/20 rounded-2xl shadow-[0_8px_30px_rgba(0,0,0,0.5)] overflow-hidden backdrop-blur-sm">
                                        <div className="px-3 pt-2.5 pb-1 text-[10px] font-bold text-primary/70 uppercase tracking-widest border-b border-purple-500/10">سطح دوره</div>
                                        {[['default','هوشمند 🤖','انتخاب خودکار'],['beginner','مقدماتی','شروع از صفر'],['intermediate','متوسط','دانش پایه'],['expert','پیشرفته','تخصصی'],['high_expert','فوق تخصصی','حرفه‌ای']].map(([val, label, sub]) => (
                                            <button
                                                key={val} type="button"
                                                onClick={() => { setLevel(val); setLevelOpen(false); }}
                                                className={`w-full text-right px-4 py-2.5 flex flex-col gap-0.5 transition-all ${
                                                    level === val
                                                        ? 'bg-primary/15 text-primary'
                                                        : 'text-slate-300 hover:bg-purple-900/30 hover:text-white'
                                                }`}
                                            >
                                                <span className="text-xs font-semibold">{label}</span>
                                                <span className="text-[10px] opacity-60">{sub}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* ── Learning Style Selector (custom popup) ── */}
                            <div className="relative">
                                <button
                                    type="button"
                                    onClick={() => { setStyleOpen(o => !o); setLevelOpen(false); }}
                                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                                        learningStyle !== 'default'
                                            ? 'bg-primary/15 border-primary/40 text-primary'
                                            : 'bg-purple-900/20 border-purple-500/15 text-slate-300 hover:border-primary/30 hover:text-slate-100'
                                    }`}
                                >
                                    <BookOpen size={13} className="shrink-0" />
                                    <span>سبک یادگیری: <span className="font-bold">{{
                                        default: 'هوشمند', practical: 'عملی',
                                        theoretical: 'تئوری', visual: 'بصری'
                                    }[learningStyle]}</span></span>
                                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-200 ${styleOpen ? 'rotate-180' : ''}`}><polyline points="6 9 12 15 18 9"/></svg>
                                </button>
                                {styleOpen && (
                                    <div className="absolute bottom-full mb-2 right-0 z-50 min-w-[160px] bg-[#1a1525] border border-purple-500/20 rounded-2xl shadow-[0_8px_30px_rgba(0,0,0,0.5)] overflow-hidden backdrop-blur-sm">
                                        <div className="px-3 pt-2.5 pb-1 text-[10px] font-bold text-primary/70 uppercase tracking-widest border-b border-purple-500/10">سبک یادگیری</div>
                                        {[['default','هوشمند 🤖','انتخاب خودکار'],['practical','عملی','پروژه‌محور'],['theoretical','تئوری','مفهومی'],['visual','بصری','ویدیو‌محور']].map(([val, label, sub]) => (
                                            <button
                                                key={val} type="button"
                                                onClick={() => { setLearningStyle(val); setStyleOpen(false); }}
                                                className={`w-full text-right px-4 py-2.5 flex flex-col gap-0.5 transition-all ${
                                                    learningStyle === val
                                                        ? 'bg-primary/15 text-primary'
                                                        : 'text-slate-300 hover:bg-purple-900/30 hover:text-white'
                                                }`}
                                            >
                                                <span className="text-xs font-semibold">{label}</span>
                                                <span className="text-[10px] opacity-60">{sub}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* ── Sessions count ── */}
                            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                                durationSessions > 0
                                    ? 'bg-primary/15 border-primary/40 text-primary'
                                    : 'bg-purple-900/20 border-purple-500/15 text-slate-300'
                            }`}>
                                <Clock size={13} className="shrink-0" />
                                <span>تعداد جلسات:</span>
                                <input
                                    type="number"
                                    min="1" max="50"
                                    value={durationSessions || ''}
                                    placeholder="هوشمند"
                                    onClick={e => e.stopPropagation()}
                                    onChange={(e) => {
                                        const val = parseInt(e.target.value);
                                        setDurationSessions(isNaN(val) ? 0 : val);
                                    }}
                                    className="bg-transparent border-0 w-12 text-center focus:ring-0 focus:outline-none placeholder:text-slate-500 p-0 font-bold"
                                />
                            </div>
                        </div>

                        {/* Input Box capsule */}
                        <div className="bg-dark-lightest/60 border border-purple-500/10 rounded-2xl p-2 shadow-xl hover:border-primary/10 focus-within:border-primary/30 transition-all flex flex-col">
                            {/* Selected Files Preview in footer */}
                            {attachedFiles.length > 0 && (
                                <div className="flex flex-wrap gap-2 mb-2 pb-2 border-b border-purple-500/5 px-1">
                                    {attachedFiles.map(file => (
                                        <div key={file.id} className="flex items-center gap-2 bg-dark border border-purple-500/10 rounded-xl p-1.5 pr-2.5 text-[10px] text-slate-300 shadow">
                                            {file.type === 'image' ? (
                                                <img src={file.data} className="w-6 h-6 rounded-md object-cover" />
                                            ) : (
                                                <div className="w-6 h-6 rounded-md bg-primary/25 flex items-center justify-center text-primary font-mono text-[8px] font-bold">صدا</div>
                                            )}
                                            <span className="max-w-[120px] truncate">{file.name}</span>
                                            <button type="button" onClick={() => removeAttachedFile(file.id)} className="text-slate-400 hover:text-red-400 p-0.5">
                                                <X size={12} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Voice Recording wave visualizer */}
                            {isRecording && (
                                <div className="flex items-center justify-between bg-red-500/10 border border-red-500/20 rounded-xl p-2 mb-2 text-red-400 text-xs animate-pulse">
                                    <div className="flex items-center gap-1.5">
                                        <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                                        <span>در حال ضبط صدا...</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="font-mono font-medium">{recordingTime} ثانیه</span>
                                        <button 
                                            type="button" 
                                            onClick={stopRecording} 
                                            className="bg-red-500 text-white px-3 py-1 rounded-md text-[10px] font-bold hover:bg-red-600 transition-all"
                                        >
                                            توقف
                                        </button>
                                    </div>
                                </div>
                            )}

                            <div className="flex items-center gap-1.5">
                                <input
                                    type="file" ref={fileInputRef} onChange={handleFileSelect} accept="image/*,audio/*" multiple className="hidden"
                                />

                                {/* Voice Record button — LEFT side */}
                                <button
                                    type="button"
                                    onClick={isRecording ? stopRecording : startRecording}
                                    disabled={isLoading}
                                    className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all shrink-0 self-center border ${
                                        isRecording
                                            ? 'bg-red-500/20 border-red-500/40 text-red-400 hover:bg-red-500/30'
                                            : 'bg-purple-900/25 border-purple-500/20 text-purple-300 hover:bg-primary/20 hover:text-primary hover:border-primary/30'
                                    }`}
                                    title="ضبط صدا"
                                >
                                    <MicIcon size={17} />
                                </button>

                                {/* Paperclip Attach button — LEFT side */}
                                <button
                                    type="button"
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={isLoading || isRecording}
                                    className="w-10 h-10 rounded-xl flex items-center justify-center transition-all shrink-0 self-center border bg-purple-900/25 border-purple-500/20 text-purple-300 hover:bg-primary/20 hover:text-primary hover:border-primary/30 disabled:opacity-40"
                                    title="پیوست تصویر یا فایل صوتی"
                                >
                                    <PaperclipIcon size={17} />
                                </button>

                                {/* Text Input field — MIDDLE (flex-1) */}
                                <input
                                    type="text" value={input} onChange={(e) => setInput(e.target.value)}
                                    placeholder={pendingCourseData ? 'تغییرات مورد نظر را بنویسید...' : 'پاسخ یا موضوع خود را بنویسید...'}
                                    className="flex-1 bg-transparent border-0 py-2.5 px-2 text-sm text-slate-200 focus:outline-none focus:ring-0 placeholder:text-slate-500 self-center min-w-0"
                                    disabled={isLoading || isRecording} autoFocus
                                    onClick={() => { setLevelOpen(false); setStyleOpen(false); }}
                                />

                                {/* Send button — RIGHT side, minimal arrow */}
                                <button
                                    type="submit"
                                    disabled={isLoading || isRecording || (!input.trim() && attachedFiles.length === 0)}
                                    className="w-10 h-10 rounded-xl bg-primary hover:bg-primary/90 active:scale-95 text-white flex items-center justify-center transition-all shrink-0 self-center shadow-[0_0_12px_rgba(168,85,247,0.35)] disabled:opacity-25 disabled:shadow-none"
                                    title="ارسال"
                                >
                                    <ArrowLeftIcon size={17} />
                                </button>
                            </div>
                        </div>
                    </form>
                    <p className="text-center text-[10px] text-slate-500 mt-2 font-mono font-medium">Powered by Blue AI Assistant</p>
                </div>
            </div>
        </div>
    );
}

// ─── Full-Screen Coach Chat Modal ──────────────────────────────────────────
function CoachFullScreenModal({ messages, input, setInput, isLoading, onSend, onMinimize, onClose, viewingItem, courseColor }) {
    const scrollRef = useRef(null);
    const vColor = courseColor;
    const prevLenRef = useRef(messages.length);

    React.useEffect(() => {
        const container = scrollRef.current;
        if (container) {
            const isNewMessage = messages.length > prevLenRef.current;
            const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 120;
            if (isNewMessage || isNearBottom || isLoading) {
                container.scrollTop = container.scrollHeight;
            }
        }
        prevLenRef.current = messages.length;
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
