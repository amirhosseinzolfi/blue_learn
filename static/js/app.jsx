const { useState, useEffect, useRef } = React;

function App() {
    // ── State ──────────────────────────────────────────────────────────────
    const [courses, setCourses] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [viewingItem, setViewingItem] = useState(null);
    const [currentView, setCurrentView] = useState('courses');
    const [dailyMicroCourses, setDailyMicroCourses] = useState([]);
    const [stats, setStats] = useState({ total_courses: 0, completed_courses: 0, total_sessions: 0, total_completed_sessions: 0, total_study_time: 0, recent_completed: [], activity_data: [] });
    const [insights, setInsights] = useState([]);
    const [isInsightLoading, setIsInsightLoading] = useState(false);
    const [settings, setSettings] = useState({ google_api_key: '', model_name: '' });
    const [settingsSaved, setSettingsSaved] = useState(false);
    const [loading, setLoading] = useState(false);
    const [loadingItemId, setLoadingItemId] = useState(null);
    const [activeMenu, setActiveMenu] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [isCoachMode, setIsCoachMode] = useState(false);
    const [isCoachFullScreen, setIsCoachFullScreen] = useState(false);
    const [coachMessages, setCoachMessages] = useState([]);
    const [coachInput, setCoachInput] = useState('');
    const [isCoachLoading, setIsCoachLoading] = useState(false);
    const [openChapters, setOpenChapters] = useState({});
    const [isSessionMenuOpen, setIsSessionMenuOpen] = useState(false);
    const [copied, setCopied] = useState(false);
    const [toast, setToast] = useState(null);
    const [isChatModalOpen, setIsChatModalOpen] = useState(false);
    const [chatMessages, setChatMessages] = useState([]);
    const [chatInput, setChatInput] = useState('');
    const [isChatLoading, setIsChatLoading] = useState(false);
    const [pendingCourseData, setPendingCourseData] = useState(null);
    const [isCourseSettingsModalOpen, setIsCourseSettingsModalOpen] = useState(false);
    const [editingCourse, setEditingCourse] = useState(null);
    const [courseSettingsForm, setCourseSettingsForm] = useState({ title: '', color: 'purple', cover_image: null, preview_image: null });
    const [microSettings, setMicroSettings] = useState(() => { const s = localStorage.getItem('micro_settings'); return s ? JSON.parse(s) : { courseIds: [], countPerCourse: 1 }; });
    const [isMicroSettingsOpen, setIsMicroSettingsOpen] = useState(false);
    const [isDailyLoading, setIsDailyLoading] = useState(false);
    const [visibleSeries, setVisibleSeries] = useState({ study: true, average: false });
    const [chartPopup, setChartPopup] = useState({ visible: false, data: null, x: 0, y: 0 });
    const [popupHovered, setPopupHovered] = useState(false);

    // ── Refs ───────────────────────────────────────────────────────────────
    const menuRef = useRef(null);
    const sessionMenuRef = useRef(null);
    const coachScrollRef = useRef(null);
    const chatScrollRef = useRef(null);
    const contentRef = useRef(null);
    const mainScrollRef = useRef(null);
    const coverImageInputRef = useRef(null);

    // ── Custom hooks ───────────────────────────────────────────────────────
    const { sidebarRatio, isDragging, startDrag } = useSidebarDrag(contentRef);

    const handleStudyTimeSync = (itemId, newTotal) => {
        // Update selectedCourse items
        setSelectedCourse(prev => {
            if (!prev) return prev;
            const updatedItems = prev.items.map(i => i.id === itemId ? { ...i, study_time: newTotal } : i);
            return { ...prev, items: updatedItems };
        });
        // Update viewingItem if it matches
        if (viewingItem?.id === itemId) {
            setViewingItem(prev => ({ ...prev, study_time: newTotal }));
        }
        // Refresh stats to update daily activity/total time
        fetchStats();
    };

    const { studyTimer, syncNow, isPaused, setIsPaused, setManualTime } = useStudyTimer(viewingItem, currentView, isCoachMode, handleStudyTimeSync);

    // ── Helpers ────────────────────────────────────────────────────────────
    const showToast = (message, type = 'success') => { setToast({ message, type }); setTimeout(() => setToast(null), 4000); };
    const scrollCoachBottom = () => setTimeout(() => { if (coachScrollRef.current) coachScrollRef.current.scrollTop = coachScrollRef.current.scrollHeight; }, 50);

    // ── Data fetching ──────────────────────────────────────────────────────
    const fetchCourses = () => api.fetchCourses().then(setCourses).catch(console.error);
    const fetchStats = () => api.fetchStats().then(setStats).catch(console.error);
    const fetchInsights = () => api.fetchInsights().then(setInsights).catch(console.error);

    const loadChatHistory = async (courseId) => {
        try {
            const hist = await api.fetchChatHistory(courseId);
            setCoachMessages(hist?.length > 0 ? hist : [{ role: 'assistant', content: 'سلام! من دستیار هوشمند شما برای این دوره هستم. اگر سوالی دارید بپرسید.' }]);
        } catch { setCoachMessages([{ role: 'assistant', content: 'سلام! من دستیار هوشمند شما برای این دوره هستم.' }]); }
    };

    const selectCourse = async (courseId, keepItem = false) => {
        setLoading(true);
        try {
            const course = await api.fetchCourse(courseId);
            setSelectedCourse(course);
            await loadChatHistory(courseId);
            if (!keepItem) { setViewingItem(null); if (mainScrollRef.current) mainScrollRef.current.scrollTo(0, 0); }
        } catch (e) { console.error(e); } finally { setLoading(false); }
    };

    const fetchDailyMicro = async (loadMore = false, settingsOverride = null) => {
        const s = settingsOverride || microSettings;
        setIsDailyLoading(true);
        try {
            const data = await api.fetchDailyMicro(s.countPerCourse, s.courseIds, loadMore ? dailyMicroCourses.map(i => i.item_id) : []);
            const todayKey = new Date().toISOString().split('T')[0];
            const storageKey = `daily_courses_${todayKey}`;
            if (loadMore) {
                setDailyMicroCourses(prev => {
                    const merged = Array.from(new Map([...prev, ...data].map(i => [i.item_id, i])).values());
                    localStorage.setItem(storageKey, JSON.stringify(merged));
                    return merged;
                });
            } else {
                setDailyMicroCourses(data);
                localStorage.setItem(storageKey, JSON.stringify(data));
            }
        } catch (e) { console.error(e); } finally { setIsDailyLoading(false); }
    };

    // ── Effects ────────────────────────────────────────────────────────────
    useEffect(() => {
        fetchCourses(); fetchStats(); fetchInsights();
        api.fetchSettings().then(d => setSettings({ google_api_key: d.google_api_key || '', model_name: d.model_name || 'gemini-flash-latest', name: d.name || '', age: d.age || '', education: d.education || '', background_experience: d.background_experience || '', additional_info: d.additional_info || '' })).catch(console.error);
        const todayKey = new Date().toISOString().split('T')[0];
        const stored = localStorage.getItem(`daily_courses_${todayKey}`);
        stored ? setDailyMicroCourses(JSON.parse(stored)) : fetchDailyMicro(false, microSettings);

        const onClickOutside = (e) => {
            if (menuRef.current && !menuRef.current.contains(e.target)) setActiveMenu(null);
            if (sessionMenuRef.current && !sessionMenuRef.current.contains(e.target)) setIsSessionMenuOpen(false);
            const popup = document.getElementById('chart-day-popup');
            if (popup && !popup.contains(e.target)) setChartPopup(p => ({ ...p, visible: false }));
        };
        document.addEventListener('mousedown', onClickOutside);
        return () => document.removeEventListener('mousedown', onClickOutside);
    }, []);

    useEffect(() => {
        if (viewingItem && contentRef.current) window.scrollTo({ top: contentRef.current.offsetTop - 20, behavior: 'smooth' });
        if (viewingItem) {
            setIsCoachMode(false);
            if (viewingItem.chapter) setOpenChapters(p => ({ ...p, [viewingItem.chapter]: true }));
            if (selectedCourse) localStorage.setItem(`last_session_${selectedCourse.id}`, viewingItem.id);
        }
    }, [viewingItem?.id]);

    useEffect(() => { if (isCoachMode) scrollCoachBottom(); }, [isCoachMode]);

    // Sync daily micro completion status with courses
    useEffect(() => {
        if (!courses.length || !dailyMicroCourses.length) return;
        let changed = false;
        const updated = dailyMicroCourses.map(daily => {
            const item = courses.find(c => c.id === daily.course_id)?.items?.find(i => i.id === daily.item_id);
            if (item && item.is_completed !== daily.is_completed) { changed = true; return { ...daily, is_completed: item.is_completed }; }
            return daily;
        });
        if (changed) {
            setDailyMicroCourses(updated);
            localStorage.setItem(`daily_courses_${new Date().toISOString().split('T')[0]}`, JSON.stringify(updated));
        }
    }, [courses]);

    // ── Action handlers ────────────────────────────────────────────────────
    const generateInsight = async () => {
        setIsInsightLoading(true);
        try { const d = await api.generateInsight(); setInsights(p => [d, ...p]); showToast('بینش جدید با موفقیت ایجاد شد!'); }
        catch { showToast('خطا در ایجاد بینش', 'error'); }
        finally { setIsInsightLoading(false); }
    };

    const generateItem = async (itemId) => {
        const target = selectedCourse.items.find(i => i.id === itemId);
        if (target) setViewingItem({ ...target, content: null });
        setLoadingItemId(itemId); setLoading(true);
        try {
            const res = await api.generateItem(itemId);
            setViewingItem(res); setLoadingItemId(null);
            const course = await api.fetchCourse(selectedCourse.id);
            setSelectedCourse(course);
            const fresh = course.items.find(i => i.id === itemId);
            if (fresh) setViewingItem(fresh);
        } catch (e) { console.error(e); } finally { setLoadingItemId(null); setLoading(false); }
    };

    const completeItem = async (itemId) => {
        await syncNow(itemId);
        try {
            await api.completeItem(itemId);
            if (viewingItem?.id === itemId) { 
                setViewingItem(v => ({ ...v, is_completed: true })); 
                showToast('تبریک! این درس با موفقیت به پایان رسید.'); 
            }
            // Update selectedCourse items locally for immediate feedback
            setSelectedCourse(prev => {
                if (!prev) return prev;
                return { ...prev, items: prev.items.map(i => i.id === itemId ? { ...i, is_completed: true } : i) };
            });
            fetchStats();
            setDailyMicroCourses(prev => {
                const updated = prev.map(i => i.item_id === itemId ? { ...i, is_completed: true } : i);
                localStorage.setItem(`daily_courses_${new Date().toISOString().split('T')[0]}`, JSON.stringify(updated));
                return updated;
            });
        } catch (e) { console.error(e); }
    };

    const handleMicroCardClick = async (item) => {
        setCurrentView('courses'); setLoading(true);
        try {
            const course = await api.fetchCourse(item.course_id);
            setSelectedCourse(course); await loadChatHistory(item.course_id);
            const target = course.items.find(i => i.id === item.item_id);
            if (!target) return;
            if (target.content) { setViewingItem(target); return; }
            setViewingItem({ ...target, content: null }); setLoadingItemId(target.id);
            const gen = await api.generateItem(target.id);
            setViewingItem(gen);
            const updated = await api.fetchCourse(item.course_id);
            setSelectedCourse(updated);
            const fresh = updated.items.find(i => i.id === target.id);
            if (fresh) setViewingItem(fresh);
            fetchStats();
        } catch (e) { console.error(e); } finally { setLoading(false); setLoadingItemId(null); }
    };

    const deleteCourse = async (id, e) => {
        e.stopPropagation();
        if (!confirm('آیا از حذف این دوره اطمینان دارید؟')) return;
        try { await api.deleteCourse(id); fetchCourses(); setActiveMenu(null); } catch (e) { console.error(e); }
    };

    const openEditCourse = (course) => {
        setEditingCourse(course);
        setCourseSettingsForm({ title: course.title, color: course.color || 'purple', cover_image: null, preview_image: course.cover_image });
        setIsCourseSettingsModalOpen(true);
        setActiveMenu(null);
    };

    const saveCourseSettings = async (e) => {
        e.preventDefault(); if (!editingCourse) return; setLoading(true);
        try {
            await api.patchCourse(editingCourse.id, { title: courseSettingsForm.title, color: courseSettingsForm.color });
            if (courseSettingsForm.cover_image) await api.uploadCover(editingCourse.id, courseSettingsForm.cover_image);
            fetchCourses();
            if (selectedCourse?.id === editingCourse.id) { const c = await api.fetchCourse(editingCourse.id); setSelectedCourse(c); }
            setIsCourseSettingsModalOpen(false); setEditingCourse(null);
        } catch (e) { console.error(e); } finally { setLoading(false); }
    };

    const sendChatMessage = async () => {
        if (!chatInput.trim() || isChatLoading) return;
        const msgs = [...chatMessages, { role: 'user', content: chatInput }];
        setChatMessages(msgs); setChatInput(''); setIsChatLoading(true); setPendingCourseData(null);
        try {
            const res = await api.chatCourseGen(msgs);
            setChatMessages(p => [...p, { role: 'assistant', content: res.chat_response }]);
            if (res.is_complete && res.course_data) setPendingCourseData(res.course_data);
        } catch { setChatMessages(p => [...p, { role: 'assistant', content: 'خطایی رخ داد. لطفا دوباره تلاش کنید.' }]); }
        finally { setIsChatLoading(false); }
    };

    const acceptCourse = async () => {
        if (!pendingCourseData) return;
        setChatMessages(p => [...p, { role: 'assistant', content: 'در حال ایجاد دوره...' }]);
        setLoading(true);
        try {
            const res = await api.post('/courses/', pendingCourseData);
            setIsChatModalOpen(false); setPendingCourseData(null);
            if (res?.id) await selectCourse(res.id);
        } catch (e) { console.error(e); } finally { setLoading(false); }
    };

    const sendCoachMessage = async () => {
        if (!coachInput.trim() || isCoachLoading || !selectedCourse || !viewingItem) return;
        const msg = coachInput;
        setCoachMessages(p => [...p, { role: 'user', content: msg }]);
        setCoachInput(''); setIsCoachLoading(true); scrollCoachBottom();
        try {
            let first = true;
            await api.coachStream(selectedCourse.id, viewingItem.id, msg, (full) => {
                setIsCoachLoading(false);
                if (first) { setCoachMessages(p => [...p, { role: 'assistant', content: full }]); first = false; }
                else setCoachMessages(p => { const n = [...p]; n[n.length - 1].content = full; return n; });
                scrollCoachBottom();
            });
        } catch { setCoachMessages(p => [...p, { role: 'assistant', content: 'خطایی رخ داد. لطفا دوباره تلاش کنید.' }]); }
        finally { setIsCoachLoading(false); }
    };

    const openChatModal = () => {
        setIsChatModalOpen(true);
        setChatMessages([{ role: 'assistant', content: 'سلام! من بلو هستم، دستیار هوشمند شما برای طراحی دوره\u200cهای آموزشی شخصی\u200cسازی شده. چه موضوعی را دوست دارید یاد بگیرید؟' }]);
        setChatInput(''); setPendingCourseData(null);
    };

    const copyContent = () => {
        if (viewingItem?.content) { navigator.clipboard.writeText(viewingItem.content); setCopied(true); setTimeout(() => setCopied(false), 2000); }
    };

    const vColor = selectedCourse ? getCourseColor(selectedCourse.color) : getCourseColor('purple');

    // Today's reading minutes from activity_data
    const todayIso = new Date().toISOString().split('T')[0];
    const todayActivity = stats.activity_data.find(d => d.date === todayIso);
    const dailyReadingMinutes = todayActivity ? todayActivity.minutes : 0;

    // ── Render ─────────────────────────────────────────────────────────────
    return (
        <div className="min-h-screen bg-dark text-slate-200 relative overflow-clip flex flex-col md:flex-row">
            {/* Toast */}
            {toast && (
                <div className="fixed top-8 left-1/2 -translate-x-1/2 z-[100] animate-in fade-in slide-in-from-top-4 duration-500">
                    <div className="bg-dark-lightest/80 backdrop-blur-xl border border-green-500/30 px-6 py-4 rounded-2xl shadow-[0_20px_40px_-10px_rgba(0,0,0,0.5)] flex items-center gap-4">
                        <div className="w-10 h-10 bg-green-500/20 rounded-xl flex items-center justify-center text-green-400">
                            <window.Icons.CheckCircle size={24} />
                        </div>
                        <p className="text-white font-bold text-sm">{toast.message}</p>
                    </div>
                </div>
            )}

            {/* Background glows */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-primary/20 blur-[100px] rounded-full" />
                <div className="absolute bottom-[-10%] left-[-10%] w-[30rem] h-[30rem] bg-indigo-500/10 blur-[120px] rounded-full" />
            </div>

            <Sidebar currentView={currentView} setCurrentView={setCurrentView} setSelectedCourse={setSelectedCourse} openChatModal={openChatModal} />

            <main ref={mainScrollRef} className="flex-1 h-screen overflow-y-auto p-4 md:p-8 relative">
                <div className="max-w-6xl mx-auto pb-12">
                    {currentView === 'courses' && (
                        <CoursesView
                            courses={courses} selectedCourse={selectedCourse} viewingItem={viewingItem} setViewingItem={setViewingItem}
                            onSelectCourse={selectCourse} onBack={() => setSelectedCourse(null)} onEditCourse={openEditCourse}
                            onDeleteCourse={deleteCourse} onGenerateItem={generateItem} onCompleteItem={completeItem}
                            onCopyContent={copyContent} onSendCoach={sendCoachMessage}
                            activeMenu={activeMenu} setActiveMenu={setActiveMenu} menuRef={menuRef}
                            sessionMenuRef={sessionMenuRef} isSessionMenuOpen={isSessionMenuOpen} setIsSessionMenuOpen={setIsSessionMenuOpen}
                            copied={copied} isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}
                            isCoachMode={isCoachMode} setIsCoachMode={setIsCoachMode}
                            isCoachFullScreen={isCoachFullScreen} setIsCoachFullScreen={setIsCoachFullScreen}
                            coachMessages={coachMessages} coachInput={coachInput} setCoachInput={setCoachInput}
                            isCoachLoading={isCoachLoading} coachScrollRef={coachScrollRef}
                            openChapters={openChapters} setOpenChapters={setOpenChapters}
                            studyTimer={studyTimer} loadingItemId={loadingItemId}
                            sidebarRatio={sidebarRatio} isDragging={isDragging} startDrag={startDrag} contentRef={contentRef}
                            isTimerPaused={isPaused} setIsTimerPaused={setIsPaused} onManualTimeUpdate={setManualTime}
                        />
                    )}
                    {currentView === 'micro' && (
                        <MicroView
                            dailyMicroCourses={dailyMicroCourses} courses={courses}
                            microSettings={microSettings} setMicroSettings={setMicroSettings}
                            onLoadMore={() => fetchDailyMicro(true)} onCardClick={handleMicroCardClick}
                            isDailyLoading={isDailyLoading}
                            onApplySettings={async () => { localStorage.setItem('micro_settings', JSON.stringify(microSettings)); setIsMicroSettingsOpen(false); await fetchDailyMicro(false, microSettings); }}
                            isMicroSettingsOpen={isMicroSettingsOpen} setIsMicroSettingsOpen={setIsMicroSettingsOpen}
                            dailyReadingMinutes={dailyReadingMinutes}
                        />
                    )}
                    {currentView === 'progress' && (
                        <ProgressView
                            stats={stats} insights={insights} isInsightLoading={isInsightLoading}
                            onGenerateInsight={generateInsight} onSessionClick={handleMicroCardClick}
                            visibleSeries={visibleSeries} setVisibleSeries={setVisibleSeries}
                            chartPopup={chartPopup} setChartPopup={setChartPopup}
                            popupHovered={popupHovered} setPopupHovered={setPopupHovered}
                            fetchStats={fetchStats}
                            showToast={showToast}
                        />
                    )}
                    {currentView === 'settings' && (
                        <SettingsView settings={settings} setSettings={setSettings} saved={settingsSaved}
                            onSave={async (e) => { e.preventDefault(); try { await api.saveSettings(settings); setSettingsSaved(true); setTimeout(() => setSettingsSaved(false), 3000); } catch (err) { console.error(err); } }}
                        />
                    )}
                </div>
            </main>

            {/* Modals */}
            {isChatModalOpen && (
                <ChatModal messages={chatMessages} input={chatInput} setInput={setChatInput} isLoading={isChatLoading}
                    onSend={sendChatMessage} onClose={() => setIsChatModalOpen(false)}
                    pendingCourseData={pendingCourseData} onAcceptCourse={acceptCourse} />
            )}
            {isCoachFullScreen && isCoachMode && (
                <CoachFullScreenModal messages={coachMessages} input={coachInput} setInput={setCoachInput}
                    isLoading={isCoachLoading} onSend={sendCoachMessage}
                    onMinimize={() => setIsCoachFullScreen(false)}
                    onClose={() => { setIsCoachFullScreen(false); setIsCoachMode(false); }}
                    viewingItem={viewingItem} courseColor={vColor} />
            )}
            {isCourseSettingsModalOpen && editingCourse && (
                <CourseSettingsModal course={editingCourse} form={courseSettingsForm} setForm={setCourseSettingsForm}
                    onSave={saveCourseSettings} onClose={() => setIsCourseSettingsModalOpen(false)}
                    loading={loading} coverInputRef={coverImageInputRef} />
            )}
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);